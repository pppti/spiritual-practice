from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AiConversation(Base):
    __tablename__ = "ai_conversation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    created_at: Mapped[str] = mapped_column(String(25), default=lambda: datetime.utcnow().isoformat())

    messages: Mapped[list["AiMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="AiMessage.created_at")


class AiMessage(Base):
    __tablename__ = "ai_message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("ai_conversation.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[str] = mapped_column(String(25), default=lambda: datetime.utcnow().isoformat())

    conversation: Mapped["AiConversation"] = relationship(back_populates="messages")
