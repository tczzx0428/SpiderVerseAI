from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

from app.api.deps import get_current_user, require_admin, get_db
from app.infra.db.models.user import User
from app.infra.db.database import SessionLocal
from app.infra.db.repos.ai_model_config_repo import AIModelConfigRepo

router = APIRouter(prefix="/api/admin/models", tags=["admin-models"])


class ModelConfigCreate(BaseModel):
    name: str
    provider: str = "deepseek"
    model_id: Optional[str] = None
    api_key: str = ""
    base_url: str = ""
    usage: str = "chat"
    is_enabled: bool = True
    priority: int = 0
    description: Optional[str] = None


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    usage: Optional[str] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class ModelConfigOut(BaseModel):
    id: int
    name: str
    provider: str
    model_id: str
    api_key: str  # 返回时会脱敏
    base_url: str
    usage: str
    is_enabled: bool
    priority: int
    description: Optional[str]
    system_prompt: Optional[str]
    created_by: int
    created_at: str

    class Config:
        from_attributes = True


def _mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _to_out(m) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "provider": m.provider,
        "model_id": m.model_id,
        "api_key": _mask_api_key(m.api_key),
        "base_url": m.base_url,
        "usage": m.usage,
        "is_enabled": m.is_enabled,
        "priority": m.priority,
        "description": m.description,
        "system_prompt": m.system_prompt,
        "created_by": m.created_by,
        "created_at": m.created_at.isoformat() if m.created_at else "",
    }


@router.get("", response_model=List[dict])
def list_models(
    enabled_only: bool = False,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)
        models = repo.list_all(enabled_only=enabled_only)
        return [_to_out(m) for m in models]
    finally:
        db.close()


@router.get("/providers")
def get_providers(admin: User = Depends(require_admin)):
    return [
        {"id": "deepseek", "name": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "models": [
            {"id": "deepseek-chat", "name": "DeepSeek V3 (对话)"},
            {"id": "deepseek-reasoner", "name": "DeepSeek R1 (推理)"},
            {"id": "deepseek-coder", "name": "DeepSeek Coder (代码)"},
        ]},
        {"id": "openai", "name": "OpenAI", "base_url": "https://api.openai.com/v1", "models": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
            {"id": "o1-mini", "name": "o1 Mini"},
        ]},
        {"id": "zhipu", "name": "智谱AI (GLM)", "base_url": "https://open.bigmodel.cn/api/paas/v4", "models": [
            {"id": "glm-4-flash", "name": "GLM-4 Flash (免费)"},
            {"id": "glm-4-plus", "name": "GLM-4 Plus"},
            {"id": "glm-4-long", "name": "GLM-4 Long (长文本)"},
            {"id": "codegeex-4", "name": "CodeGeeX-4 (代码)"},
        ]},
        {"id": "qwen", "name": "通义千问", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "models": [
            {"id": "qwen-plus", "name": "Qwen Plus"},
            {"id": "qwen-max", "name": "Qwen Max"},
            {"id": "qwen-coder-plus", "name": "Qwen Coder Plus"},
            {"id": "qwen-vl-max", "name": "Qwen VL Max (视觉)"},
        ]},
        {"id": "custom", "name": "自定义/其他", "base_url": "", "models": []},
    ]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_model(
    body: ModelConfigCreate,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)

        data = body.model_dump()
        if not data.get("model_id"):
            data["model_id"] = data["name"]

        model = repo.create(data, created_by=admin.id)
        return _to_out(model)
    finally:
        db.close()


@router.get("/{model_id}", response_model=dict)
def get_model(
    model_id: int,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)
        model = repo.get(model_id)
        if not model:
            raise HTTPException(404, "模型配置不存在")
        return _to_out(model)
    finally:
        db.close()


@router.put("/{model_id}", response_model=dict)
def update_model(
    model_id: int,
    body: ModelConfigUpdate,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)
        model = repo.update(model_id, body.model_dump(exclude_none=True))
        if not model:
            raise HTTPException(404, "模型配置不存在")
        return _to_out(model)
    finally:
        db.close()


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: int,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)
        if not repo.delete(model_id):
            raise HTTPException(404, "模型配置不存在")
    finally:
        db.close()


@router.post("/{model_id}/toggle", response_model=dict)
def toggle_model(
    model_id: int,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)
        model = repo.toggle(model_id)
        if not model:
            raise HTTPException(404, "模型配置不存在")
        return _to_out(model)
    finally:
        db.close()


class SystemPromptUpdate(BaseModel):
    system_prompt: str


@router.get("/{model_id}/system-prompt", response_model=dict)
def get_system_prompt(
    model_id: int,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)
        model = repo.get(model_id)
        if not model:
            raise HTTPException(404, "模型配置不存在")
        return {
            "id": model.id,
            "name": model.name,
            "system_prompt": model.system_prompt or "",
        }
    finally:
        db.close()


@router.put("/{model_id}/system-prompt", response_model=dict)
def update_system_prompt(
    model_id: int,
    body: SystemPromptUpdate,
    admin: User = Depends(require_admin)
):
    db = SessionLocal()
    try:
        repo = AIModelConfigRepo(db)
        model = repo.update(model_id, {"system_prompt": body.system_prompt})
        if not model:
            raise HTTPException(404, "模型配置不存在")
        return {
            "id": model.id,
            "name": model.name,
            "system_prompt": model.system_prompt,
            "message": "系统提示词更新成功",
        }
    finally:
        db.close()