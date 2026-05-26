import json
import httpx
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def _is_available() -> bool:
    return bool(ANTHROPIC_API_KEY)


async def call_claude(system_prompt: str, messages: list[dict], max_tokens: int = 1000) -> str:
    """Generic Claude API call used by chat, summarize, and auto-entry."""
    if not _is_available():
        return "[AI 未配置] 请设置 ANTHROPIC_API_KEY 环境变量以启用 AI 功能。"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": messages,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            return f"[AI 错误: {response.status_code}]"
    except Exception as e:
        return f"[AI 错误: {str(e)[:100]}]"


# ─── Cultivation Message (existing) ───

MESSAGE_PROMPT = """你是一位智慧的修行导师，精通佛道经典和心性修养。用户会提供最近一段时间的修行记录（包括日记、心情、修行时长等），请你根据这些数据，写一段150-300字的"修行寄语"。

要求：
- 语言优美，带有古典中文的韵味但不晦涩
- 结合用户实际的修行情况，给予有针对性的鼓励和指引
- 可以引用一句相关的佛道经典
- 语气温暖而坚定，如师长般的关怀
- 不要空洞的套话，要有具体的观察和建议"""


async def generate_cultivation_message(practices: list[dict], total_count: int, moods: dict, period_start: str, period_end: str) -> str:
    if total_count == 0:
        return _fallback_template(total_count, moods, period_start, period_end)

    practice_summary = "\n".join([
        f"- {p['date']}: {p['title'] or '无标题'} | 心情：{p['mood'] or '未记录'} | 时长：{p['duration_minutes']}分钟\n  {p['body'][:200]}"
        for p in practices
    ])

    user_message = f"""时间范围：{period_start} 至 {period_end}
修行次数：{total_count} 次
心情分布：{moods or '未记录'}

修行日记摘要：
{practice_summary}

请根据以上修行记录，写一段修行寄语。"""

    if not _is_available():
        return _fallback_template(total_count, moods, period_start, period_end)

    result = await call_claude(MESSAGE_PROMPT, [{"role": "user", "content": user_message}], max_tokens=600)
    if result.startswith("[AI"):
        return _fallback_template(total_count, moods, period_start, period_end)
    return result


def _fallback_template(total_count: int, moods: dict, period_start: str, period_end: str) -> str:
    dominant_mood = max(moods, key=moods.get) if moods else "平和"
    mood_names = {"calm": "平静", "energized": "精力充沛", "scattered": "散乱", "peaceful": "安宁", "tired": "疲惫"}
    mood_cn = mood_names.get(dominant_mood, dominant_mood)

    templates = [
        f"过去这段时间（{period_start} 至 {period_end}），你共修习了 {total_count} 次。你的主要心境是「{mood_cn}」。\n\n修行不在多，贵在持之以恒。每一次静坐、每一次觉察，都是在心田播下觉悟的种子。{mood_cn}的状态本身即是修行的镜子，映照出你内在的真实。\n\n《道德经》云：「为学日益，为道日损。」修行的路上，不在于积累多少知识，而在于放下多少执着。请继续安住于当下，以平常心观照每一个念头。",
        f"在 {period_start} 到 {period_end} 这段时间里，你完成了 {total_count} 次修行记录，心境以「{mood_cn}」为主。\n\n修行的本质是认识自己。每一篇日记都是一面明镜，照见内心的波澜与宁静。不必追求完美的修行状态，{'散乱时知道散乱' if dominant_mood == 'scattered' else '平静时知道平静'}，这便是正念的力量。\n\n六祖惠能说：「本来无一物，何处惹尘埃。」愿你在日常中保持这份觉知，不为外境所转。",
        f"回望 {period_start} 至 {period_end}，{total_count} 次修行，{mood_cn}常伴。\n\n修行如登山，有缓坡也有陡崖。重要的是脚步不停，心念不退。你已经在路上，这本身就值得赞叹。\n\n庄子曰：「安时而处顺，哀乐不能入也。」愿你以安时处顺之心，面对修行中的一切起伏。",
    ]
    return templates[total_count % len(templates)]


# ─── Chat ───

CHAT_SYSTEM = """你是一位修行导师，法号"觉明"，精通佛道经典，也理解现代人的生活困境。
你的回答应当：
- 温暖而睿智，如师长般循循善诱
- 适当引用佛道经典（《金刚经》《心经》《道德经》《庄子》等）
- 简短有力，一般不超过 200 字
- 使用中文，带有淡淡的古典韵味但不晦涩
- 如果用户询问修行相关问题，结合经典给出指引
- 如果用户只是聊天，保持亲切自然
- 不要使用"作为AI"之类的表述"""

CHAT_WITH_DATA_SYSTEM = """你是一位修行导师，法号"觉明"。你可以访问用户的修行数据。

请根据用户的修行统计和记录，给出个性化的建议和回答。
- 引用用户的实际修行频率、心情变化等数据
- 给出有针对性的鼓励和建议
- 引用相关佛道经典"""


async def chat_reply(history: list[dict], user_message: str, practice_context: str = "") -> str:
    """Generate chat reply, optionally with user's practice data context."""
    messages = []
    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    system = CHAT_WITH_DATA_SYSTEM if practice_context else CHAT_SYSTEM
    if practice_context:
        messages.insert(0, {"role": "user", "content": f"[系统数据]\n{practice_context}\n[/系统数据]\n好的，请根据以上数据回答后续问题。"})

    return await call_claude(system, messages, max_tokens=800)


# ─── Summarize ───

SUMMARIZE_PROMPT = """你是一位修行记录分析师。用户提供多篇修行日记，请生成一份简洁的汇总：

格式要求：
1. 先给总体评价（1-2句）
2. 心情变化趋势
3. 主要收获和亮点
4. 修行建议（1-2条）
5. 总字数控制在200字以内"""