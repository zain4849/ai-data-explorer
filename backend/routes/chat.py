"""Chat persistence routes: threads and messages stored server-side."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..models.base import get_session
from ..models.chat import ChatMessage, ChatThread
from ..models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class DatasetInfoSchema(BaseModel):
    preview: list[dict] = []
    row_count: int
    columns: list[str]
    dataset_id: str | None = None
    table_name: str | None = None

class ThreadCreate(BaseModel):
    title: str = "New Chat"


class ThreadUpdate(BaseModel):
    title: str | None = None


class MessageCreate(BaseModel):
    role: str
    content: str = ""
    sql: str | None = None
    result_json: str | None = None
    chart_html: str | None = None
    insights: str | None = None
    explanation: str | None = None
    file_name: str | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sql: str | None = None
    result_json: str | None = None
    chart_html: str | None = None
    insights: str | None = None
    explanation: str | None = None
    file_name: str | None = None
    created_at: str


class ThreadResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageResponse]
    # dataset_info: DatasetInfoSchema | None


class ThreadListItem(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str
    # dataset_info: DatasetInfoSchema | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/threads", response_model=list[ThreadListItem])
def list_threads(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rows = session.execute( # sends query to the db -> returns result object
        select(ChatThread) # SELECT * FROM chat_thread
        .where(ChatThread.user_id == user.id) # WHERE user_id = 42
        .order_by(ChatThread.updated_at.desc())
    ).scalars().all() # .scalars() -> extracts the actual ORM objs from the result, .all() converts it to a python list

    return [
        ThreadListItem(
            id=t.id,
            title=t.title,
            message_count=len(t.messages), # messages exist on the t python object, not as col in pgAdmin
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else "",
        )
        for t in rows # t = thread
    ]


@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
def create_thread(
    body: ThreadCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    thread = ChatThread(user_id=user.id, title=body.title)
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return _thread_response(thread)


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
def get_thread(
    thread_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    thread = session.get(ChatThread, thread_id) # SELECT * FROM chat_thread WHERE id = 2;
    if thread is None or thread.user_id != user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    return _thread_response(thread)


@router.put("/threads/{thread_id}", response_model=ThreadResponse)
def update_thread(
    thread_id: str,
    body: ThreadUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    thread = session.get(ChatThread, thread_id)
    if thread is None or thread.user_id != user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    if body.title is not None:
        thread.title = body.title
    # if body.dataset_id is not None:
    #     thread.dataset_id = body.dataset_id
    session.commit()
    session.refresh(thread)
    return _thread_response(thread)


@router.delete("/threads/{thread_id}", status_code=204)
def delete_thread(
    thread_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    thread = session.get(ChatThread, thread_id)
    if thread is None or thread.user_id != user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    session.delete(thread)
    session.commit()


@router.post("/threads/{thread_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_message(
    thread_id: str,
    body: MessageCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    thread = session.get(ChatThread, thread_id)
    if thread is None or thread.user_id != user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    msg = ChatMessage(
        thread_id=thread_id,
        role=body.role,
        content=body.content,
        sql=body.sql,
        result_json=body.result_json,
        chart_html=body.chart_html,
        insights=body.insights,
        explanation=body.explanation,
        file_name=body.file_name,
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return _message_response(msg)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _message_response(m: ChatMessage) -> MessageResponse:
    return MessageResponse(
        id=m.id,
        role=m.role,
        content=m.content,
        sql=m.sql,
        result_json=m.result_json,
        chart_html=m.chart_html,
        insights=m.insights,
        explanation=m.explanation,
        file_name=m.file_name,
        created_at=m.created_at.isoformat() if m.created_at else "",
    )


def _thread_response(t: ChatThread) -> ThreadResponse:
    return ThreadResponse(
        id=t.id,
        title=t.title,
        created_at=t.created_at.isoformat() if t.created_at else "",
        updated_at=t.updated_at.isoformat() if t.updated_at else "",
        messages=[_message_response(m) for m in t.messages],
    )
