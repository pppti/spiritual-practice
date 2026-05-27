from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.practice import PracticeRecord
from app.models.ai_conversation import AiConversation, AiMessage
from app.schemas.ai import (
    ChatRequest, ChatResponse, AutoEntryRequest, AutoEntryResponse,
    SummarizeRequest, SummarizeResponse,
    AiConversationResponse, AiConversationListResponse, AiMessageResponse,
)
from app.services.ai_service import call_claude, SUMMARIZE_PROMPT, CHAT_SYSTEM, CHAT_WITH_DATA_SYSTEM
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Strict positive-response rules enforced by system prompt
SAFETY_RULES = """
【核心规则——必须严格遵守】
1. 所有回复必须是正向、建设性、鼓励性的。绝不能有任何负面、消极、打击用户的表述。
2. 如果用户表达了困扰、痛苦或负面情绪，先共情，再引导向积极方向。
3. 绝不涉及政治、暴力、色情、违法内容。如果被问到，温和地引导回修行话题。
4. 不要给出任何可能伤害用户身心健康的建议。
5. 不要做任何医学诊断或治疗建议。如果涉及健康问题，建议咨询专业医生。
6. 保持修行导师的角色，不评判用户的修行方式，不比较高低深浅。
7. 回复以积极正向的引导结尾。
"""


# ─── Chat ───

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get or create conversation
    conv = None
    if req.conversation_id:
        r = await db.execute(select(AiConversation).where(AiConversation.id == req.conversation_id))
        conv = r.scalar_one_or_none()

    if not conv:
        title = req.message[:30] + ("..." if len(req.message) > 30 else "")
        conv = AiConversation(title=title)
        db.add(conv)
        await db.flush()

    # Save user message
    user_msg = AiMessage(conversation_id=conv.id, role="user", content=req.message)
    db.add(user_msg)

    # Load history
    r = await db.execute(
        select(AiMessage).where(AiMessage.conversation_id == conv.id).order_by(AiMessage.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in r.scalars().all()]

    # Build practice context if analysis mode
    practice_context = ""
    system = CHAT_SYSTEM + SAFETY_RULES
    if req.mode == "analysis":
        practice_context = await _build_practice_context(db)
        system = CHAT_WITH_DATA_SYSTEM + SAFETY_RULES

    messages_for_api = []
    for h in history[-20:]:
        messages_for_api.append({"role": h["role"], "content": h["content"]})

    if practice_context:
        system_msg = f"[系统数据]\n{practice_context}\n[/系统数据]\n好的，请根据以上数据回答后续问题。"
        messages_for_api = [{"role": "user", "content": system_msg}] + messages_for_api[-10:]

    reply = await call_claude(system, messages_for_api, max_tokens=800)

    # Save assistant message
    assistant_msg = AiMessage(conversation_id=conv.id, role="assistant", content=reply)
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(conversation_id=conv.id, reply=reply)


# ─── Conversations ───

@router.get("/conversations", response_model=AiConversationListResponse)
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(AiConversation)
        .options(selectinload(AiConversation.messages))
        .order_by(AiConversation.created_at.desc())
        .limit(30)
    )
    convs = r.unique().scalars().all()
    return AiConversationListResponse(items=[_conv_to_response(c) for c in convs])


@router.get("/conversations/{conv_id}", response_model=AiConversationResponse)
async def get_conversation(
    conv_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(AiConversation)
        .options(selectinload(AiConversation.messages))
        .where(AiConversation.id == conv_id)
    )
    conv = r.unique().scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return _conv_to_response(conv)


@router.delete("/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conv_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(AiConversation).where(AiConversation.id == conv_id))
    conv = r.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await db.delete(conv)
    await db.commit()


# ─── Summarize ───

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    req: SummarizeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.practice_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No practice IDs provided")

    r = await db.execute(
        select(PracticeRecord).where(PracticeRecord.id.in_(req.practice_ids))
    )
    practices = r.scalars().all()

    summary_text = "\n\n".join([
        f"[{p.practice_date}] {p.title or '无标题'} | 心情:{p.mood or '-'} | 分类:{p.category or '-'}\n{p.body}"
        for p in practices
    ])

    user_msg = f"请汇总以下{len(practices)}篇修行日记：\n\n{summary_text}"
    summary = await call_claude(SUMMARIZE_PROMPT + SAFETY_RULES, [{"role": "user", "content": user_msg}], max_tokens=500)
    return SummarizeResponse(summary=summary)


# ─── Auto Entry ───

AUTO_ENTRY_PROMPT = """用户提供了一段文字描述，请从中提取修行日记的结构化信息。
返回纯JSON格式（不要markdown代码块）：
{
  "title": "简短的标题",
  "body": "整理后的日记正文，润色流畅但保留原意",
  "mood": "calm/energized/scattered/peaceful/tired 中选一个最匹配的，没有则null",
  "duration_minutes": 数字或null,
  "category": "meditation/chanting/reading/walking/yoga/other 中选一个",
  "suggested_tags": ["标签1", "标签2"]
}"""


@router.post("/auto-entry", response_model=AutoEntryResponse)
async def auto_entry(
    req: AutoEntryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import json
    reply = await call_claude(AUTO_ENTRY_PROMPT, [{"role": "user", "content": req.text}], max_tokens=500)

    try:
        # Try to parse JSON from the reply
        reply_clean = reply.strip()
        if reply_clean.startswith("```"):
            reply_clean = reply_clean.split("\n", 1)[1].rsplit("\n```")[0]
        data = json.loads(reply_clean)
        return AutoEntryResponse(
            title=data.get("title", ""),
            body=data.get("body", req.text),
            mood=data.get("mood"),
            duration_minutes=data.get("duration_minutes"),
            category=data.get("category"),
            suggested_tags=data.get("suggested_tags", []),
        )
    except (json.JSONDecodeError, KeyError):
        return AutoEntryResponse(
            title="",
            body=req.text,
            suggested_tags=[],
        )


# ─── Smart Import ───

IMPORT_PROMPT = """用户提供了一段文字内容（可能是语音转文字、课程笔记、感悟记录等）。
请分析内容，提取并整理成结构化的修行日记。

首先判断内容类型（content_type）：修行感悟/课程笔记/经典摘录/日常记录/其它

返回纯JSON格式（不要markdown代码块）：
{
  "title": "简短的标题",
  "body": "整理后的正文，保留关键信息，语句通顺流畅",
  "category": "meditation/chanting/reading/walking/yoga/other 中选一个",
  "mood": "calm/energized/scattered/peaceful/tired 中选一个，没有则null",
  "suggested_tags": ["标签1", "标签2"],
  "content_type": "修行感悟"
}"""


@router.post("/import", response_model=AutoEntryResponse)
async def smart_import(
    req: AutoEntryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import json
    reply = await call_claude(IMPORT_PROMPT, [{"role": "user", "content": req.text}], max_tokens=600)

    try:
        reply_clean = reply.strip()
        if reply_clean.startswith("```"):
            reply_clean = reply_clean.split("\n", 1)[1].rsplit("\n```")[0]
        data = json.loads(reply_clean)
        return AutoEntryResponse(
            title=data.get("title", ""),
            body=data.get("body", req.text),
            mood=data.get("mood"),
            duration_minutes=None,
            category=data.get("category"),
            suggested_tags=data.get("suggested_tags", []),
        )
    except (json.JSONDecodeError, KeyError):
        return AutoEntryResponse(
            title="",
            body=req.text,
            suggested_tags=[],
        )


# ─── Helpers ───

async def _build_practice_context(db: AsyncSession) -> str:
    # Total
    total_r = await db.execute(select(func.count(PracticeRecord.id)))
    total = total_r.scalar() or 0

    # Recent 5 entries
    r = await db.execute(
        select(PracticeRecord).order_by(PracticeRecord.practice_date.desc()).limit(5)
    )
    recent = r.scalars().all()

    # Mood
    mood_r = await db.execute(
        select(PracticeRecord.mood, func.count(PracticeRecord.id))
        .where(PracticeRecord.mood.isnot(None))
        .group_by(PracticeRecord.mood)
    )
    moods = {row[0]: row[1] for row in mood_r.all()}

    # Streak
    from datetime import date, timedelta
    streak = 0
    today = date.today()
    while True:
        d = (today - timedelta(days=streak)).isoformat()
        r = await db.execute(select(PracticeRecord.id).where(PracticeRecord.practice_date == d).limit(1))
        if r.scalar_one_or_none():
            streak += 1
        else:
            break

    lines = [f"总修行次数: {total}", f"连续天数: {streak}", f"心情分布: {moods}", "", "最近日记:"]
    for p in recent:
        lines.append(f"- [{p.practice_date}] {p.title or '无标题'} | 心情:{p.mood or '-'} | 分类:{p.category or '-'} | {p.body[:100]}")
    return "\n".join(lines)


def _conv_to_response(c: AiConversation) -> AiConversationResponse:
    return AiConversationResponse(
        id=c.id,
        title=c.title,
        created_at=c.created_at,
        messages=[
            AiMessageResponse(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
            for m in c.messages
        ],
    )
