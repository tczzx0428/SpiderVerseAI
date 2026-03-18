from __future__ import annotations
from typing import Protocol


class IAppRuntime(Protocol):
    app_type: str  # 'streamlit', 'flask', 'node'

    def generate_dockerfile(self, slug: str, build_path: str) -> str: ...
    def get_entrypoint_files(self) -> list[tuple[str, str]]: ...
    def validate_structure(self, file_names: set[str]) -> tuple[bool, str]: ...
    def get_container_port(self) -> int: ...


class RuntimeRegistry:
    def __init__(self) -> None:
        self._runtimes: dict[str, IAppRuntime] = {}

    def register(self, runtime: IAppRuntime) -> None:
        self._runtimes[runtime.app_type] = runtime

    def get(self, app_type: str) -> IAppRuntime:
        rt = self._runtimes.get(app_type)
        if not rt:
            raise ValueError(f"未知的应用类型: {app_type}")
        return rt

    def list_types(self) -> list[str]:
        return list(self._runtimes.keys())
