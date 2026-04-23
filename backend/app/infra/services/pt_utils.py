"""PulseTeach AI 平台工具库 - 自动注入到每个应用容器中。
提供标准的结果文件保存接口，确保历史记录可追踪。
"""
import json
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

DATA_DIR = Path("/app/data")
RESULTS_DIR = DATA_DIR / "results"


def _get_username():
    try:
        import streamlit as st
        return st.query_params.get("pt_user", "")
    except Exception:
        return ""


def save_result(filename: str, data, subdir: str = "results", summary: str = "") -> Path:
    target_dir = DATA_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / filename

    if isinstance(data, BytesIO):
        data.seek(0)
        filepath.write_bytes(data.read())
        data.seek(0)
    elif isinstance(data, bytes):
        filepath.write_bytes(data)
    elif isinstance(data, str):
        filepath.write_text(data, encoding="utf-8")
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    _write_meta(filename, summary)
    return filepath


def _write_meta(filename: str, summary: str = ""):
    try:
        ts_match = re.search(r"(\d{8}_\d{6})", filename)
        if ts_match:
            ts_key = ts_match.group(1)
            history_dir = DATA_DIR / "history"
            history_dir.mkdir(parents=True, exist_ok=True)
            meta_path = history_dir / f"{ts_key}.json"
            if not meta_path.exists():
                meta = {
                    "run_id": ts_key,
                    "username": _get_username(),
                    "timestamp": datetime.now().isoformat(),
                    "summary": summary or filename,
                }
                meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def make_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
