from __future__ import annotations
from typing import Optional

from app.core.entities.prompt import PromptEntity
from app.core.errors import PromptNotFound
from app.core.ports.prompt_repo import IPromptRepo


class ListPrompts:
    def __init__(self, prompt_repo: IPromptRepo) -> None:
        self._prompt_repo = prompt_repo

    def execute(self, category: Optional[str] = None) -> list[PromptEntity]:
        return self._prompt_repo.list(category=category)

    def list_categories(self) -> list[str]:
        return self._prompt_repo.list_categories()


class CreatePrompt:
    def __init__(self, prompt_repo: IPromptRepo) -> None:
        self._prompt_repo = prompt_repo

    def execute(self, title: str, content: str, category: Optional[str] = None,
                sort_order: int = 0, created_by: Optional[int] = None) -> PromptEntity:
        entity = PromptEntity(
            id=0, title=title, content=content,
            category=category, sort_order=sort_order, created_by=created_by,
        )
        return self._prompt_repo.create(entity)


class UpdatePrompt:
    def __init__(self, prompt_repo: IPromptRepo) -> None:
        self._prompt_repo = prompt_repo

    def execute(self, prompt_id: int, **kwargs) -> PromptEntity:
        prompt = self._prompt_repo.get(prompt_id)
        if not prompt:
            raise PromptNotFound(prompt_id)
        for k, v in kwargs.items():
            if v is not None:
                setattr(prompt, k, v)
        return self._prompt_repo.update(prompt)


class DeletePrompt:
    def __init__(self, prompt_repo: IPromptRepo) -> None:
        self._prompt_repo = prompt_repo

    def execute(self, prompt_id: int) -> None:
        if not self._prompt_repo.get(prompt_id):
            raise PromptNotFound(prompt_id)
        self._prompt_repo.delete(prompt_id)
