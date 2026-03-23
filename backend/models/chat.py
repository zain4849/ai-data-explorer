"""Chat persistence models: threads and messages stored server-side per user."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: str = Column(String, ForeignKey("users.id"), nullable=False)
    # dataset_id: str = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True)
    title: str = Column(String, default="New Chat")
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages = relationship(
        "ChatMessage", # The messages attribute will contain objects of type ChatMessage.
        back_populates="thread", # The other side of this relationship is stored in the attribute called thread, thread = ... which then allows thread.messages & message.thread
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    owner = relationship("User", backref="chat_threads")

    # dataset_id: str | None = Column(String, ForeignKey("datasets.id"), nullable=True)
    
    # dataset_info = relationship(
    #     "Dataset",
    #     foreign_keys=[dataset_id],
    # )
'''
thread.messages = [
    ChatMessage(...),
    ChatMessage(...),
    ChatMessage(...)
]
'''


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid4()))
    thread_id: str = Column(String, ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    role: str = Column(String, nullable=False)
    content: str = Column(Text, nullable=False, default="")
    sql: str | None = Column(Text)
    result_json: str | None = Column(Text)
    chart_html: str | None = Column(Text)
    insights: str | None = Column(Text)
    explanation: str | None = Column(Text)
    file_name: str | None = Column(String)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Assume you have msg = returns ChatMessage object (row)
    # Below is equal to thread = msg.thread
    thread = relationship("ChatThread", back_populates="messages")
