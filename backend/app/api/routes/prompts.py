from __future__ import annotations
from fastapi import APIRouter, Depends, status

from app.api.deps import get_container, get_current_user, require_admin
from app.api.schemas.prompt import PromptCreate, PromptOut, PromptUpdate
from app.container import Container
from app.infra.db.models.user import User

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptOut])
def list_prompts(category: str = None, c: Container = Depends(get_container),
                 current_user: User = Depends(get_current_user)):
    prompts = c.list_prompts.execute(category=category)
    return [PromptOut.model_validate(p) for p in prompts]


@router.get("/categories")
def list_categories(c: Container = Depends(get_container),
                    current_user: User = Depends(get_current_user)):
    return c.list_prompts.list_categories()


@router.post("", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
def create_prompt(body: PromptCreate, c: Container = Depends(get_container),
                  admin: User = Depends(require_admin)):
    prompt = c.create_prompt.execute(
        title=body.title, content=body.content,
        category=body.category, sort_order=body.sort_order,
        created_by=admin.id,
    )
    return PromptOut.model_validate(prompt)


@router.put("/{prompt_id}", response_model=PromptOut)
def update_prompt(prompt_id: int, body: PromptUpdate,
                  c: Container = Depends(get_container),
                  admin: User = Depends(require_admin)):
    prompt = c.update_prompt.execute(prompt_id, **body.model_dump(exclude_none=True))
    return PromptOut.model_validate(prompt)


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: int, c: Container = Depends(get_container),
                  admin: User = Depends(require_admin)):
    c.delete_prompt.execute(prompt_id)
