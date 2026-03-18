from __future__ import annotations
from pathlib import Path


DOCKERFILE_TEMPLATE = """\
FROM iregistry.baidu-int.com/baidu-base/python:3.11
WORKDIR /app
ENV PYTHONPATH=/app

# 安装 pip 并升级
RUN python -m ensurepip --upgrade 2>/dev/null || true && python -m pip install --upgrade pip

# 安装应用依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制用户应用代码
COPY . .

# 注入平台文件（放在 COPY . . 之后，确保不被用户文件覆盖）
COPY pe_entry.py /app/pe_entry.py
COPY pe_utils.py /app/pe_utils.py

# 将用户的 app.py 重命名，由追踪入口代理执行
RUN mv /app/app.py /app/app_original.py

EXPOSE 8501
CMD ["streamlit", "run", "pe_entry.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.baseUrlPath=/apps/{slug}", \
     "--browser.gatherUsageStats=false"]
"""


class StreamlitRuntime:
    app_type: str = "streamlit"

    def generate_dockerfile(self, slug: str, build_path: str) -> str:
        return DOCKERFILE_TEMPLATE.format(slug=slug)

    def get_entrypoint_files(self) -> list[tuple[str, str]]:
        src_dir = Path(__file__).parent.parent.parent / "infra" / "services"
        files = []
        for fname in ("pe_entry.py", "pe_utils.py"):
            src = src_dir / fname
            if src.exists():
                files.append((fname, src.read_text(encoding="utf-8")))
        return files

    def validate_structure(self, file_names: set[str]) -> tuple[bool, str]:
        required = {"app.py", "requirements.txt"}
        missing = required - file_names
        if missing:
            return False, f"缺少必要文件: {', '.join(missing)}"
        return True, ""

    def get_container_port(self) -> int:
        return 8501
