from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str
    mode: str = "general"  # 'general' or 'analysis'


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str


class AutoEntryRequest(BaseModel):
    text: str


class AutoEntryResponse(BaseModel):
    title: str
    body: str
    mood: str | None = None
    duration_minutes: int | None = None
    suggested_tags: list[str] = []


class SummarizeRequest(BaseModel):
    practice_ids: list[int]


class SummarizeResponse(BaseModel):
    summary: str


# Conversation list/detail
class AiMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class AiConversationResponse(BaseModel):
    id: int
    title: str
    created_at: str
    messages: list[AiMessageResponse] = []


class AiConversationListResponse(BaseModel):
    items: list[AiConversationResponse]
