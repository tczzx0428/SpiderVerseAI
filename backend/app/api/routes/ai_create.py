from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.infra.db.models.user import User
from app.infra.db.database import SessionLocal
from app.infra.db.repos.ai_creation_repo import AICreationRepo
from app.core.usecases.ai_create import AIChatService, AutoDeployService

router = APIRouter(prefix="/api/ai-create", tags=["ai-create"])

_ai_chat = AIChatService()
_auto_deploy = AutoDeployService()


class ChatRequest(BaseModel):
    creation_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    conversation: list


class StartCreateRequest(BaseModel):
    creation_id: int


class CreationOut(BaseModel):
    id: int
    title: Optional[str]
    status: str
    progress: int
    progress_message: Optional[str]
    error_message: Optional[str]
    app_id: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


@router.post("/new", response_model=CreationOut, status_code=201)
def create_new_session(
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        repo = AICreationRepo(db)
        creation = repo.create(user_id=current_user.id, title=title)
        return _to_out(creation)
    finally:
        db.close()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest,
         current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        repo = AICreationRepo(db)
        creation = repo.get(req.creation_id)

        if not creation:
            raise HTTPException(404, "会话不存在")
        if creation.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(403, "无权访问此会话")
        if creation.status not in ("chatting",):
            raise HTTPException(400, f"当前状态 {creation.status} 不允许对话")

        conversation = creation.conversation or []
        conversation.append({"role": "user", "content": req.message})

        reply = _ai_chat.chat(conversation, req.message)
        conversation.append({"role": "assistant", "content": reply})

        repo.update_conversation(req.creation_id, conversation)

        return ChatResponse(reply=reply, conversation=conversation)
    finally:
        db.close()


@router.post("/start", status_code=202)
def start_creation(req: StartCreateRequest,
                   current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        repo = AICreationRepo(db)
        creation = repo.get(req.creation_id)

        if not creation:
            raise HTTPException(404, "会话不存在")
        if creation.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(403, "无权操作此会话")
        if creation.status != "chatting":
            raise HTTPException(400, f"当前状态 {creation.status} 无法开始创建")

        conversation = creation.conversation or []

        repo.update_status(req.creation_id, "generating", progress=5,
                           message="正在分析需求...")

        requirements = _ai_chat.extract_requirements(conversation)

        repo.update_status(req.creation_id, "generating", progress=10,
                           message="正在生成代码...")

        generated_code = _ai_chat.generate_code(requirements)

        repo.update_status(req.creation_id, "generating", progress=20,
                           message="代码生成完成，开始部署...",
                           generated_code=generated_code)

        _auto_deploy.start_deploy(
            creation_id=req.creation_id,
            user_id=current_user.id,
            requirements=requirements,
            generated_code=generated_code,
        )

        return {
            "message": "已开始创建应用",
            "creation_id": req.creation_id,
            "status": "generating",
            "requirements": requirements,
        }
    finally:
        db.close()


@router.get("/{creation_id}", response_model=CreationOut)
def get_status(creation_id: int,
               current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        repo = AICreationRepo(db)
        creation = repo.get(creation_id)

        if not creation:
            raise HTTPException(404, "会话不存在")
        if creation.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(403, "无权访问此会话")

        return _to_out(creation)
    finally:
        db.close()


@router.get("", response_model=list[CreationOut])
def list_creations(limit: int = 20,
                   current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        repo = AICreationRepo(db)
        creations = repo.list_by_user(current_user.id, limit)
        return [_to_out(c) for c in creations]
    finally:
        db.close()


@router.delete("/{creation_id}", status_code=204)
def delete_creation(creation_id: int,
                    current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        repo = AICreationRepo(db)
        creation = repo.get(creation_id)

        if not creation:
            raise HTTPException(404, "会话不存在")
        if creation.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(403, "无权删除此会话")

        repo.delete(creation_id)
    finally:
        db.close()


def _to_out(c) -> CreationOut:
    return CreationOut(
        id=c.id,
        title=c.title,
        status=c.status,
        progress=c.progress,
        progress_message=c.progress_message,
        error_message=c.error_message,
        app_id=c.app_id,
        created_at=c.created_at.isoformat() if c.created_at else "",
    )