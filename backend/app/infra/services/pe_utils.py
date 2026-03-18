"""PE Space 平台工具库 - 自动注入到每个应用容器中。
提供标准的结果文件保存接口，确保历史记录可追踪。
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from io import BytesIO


DATA_DIR = Path("/app/data")
RESULTS_DIR = DATA_DIR / "results"


def _get_username():
    try:
        import streamlit as st
        return st.query_params.get("pe_user", "")
    except Exception:
        return ""


def save_result(filename: str, data, subdir: str = "results", summary: str = "") -> Path:
    """保存结果文件到 /app/data/{subdir}/，并自动写入元数据 JSON。

    Args:
        filename: 文件名（如 "batch_result_20260316_110211.xlsx"）
        data: 文件内容，可以是 bytes、BytesIO 或 str
        subdir: 子目录名，默认 "results"
        summary: 运行摘要，为空时使用文件名
    """
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
    """从文件名提取时间戳，写入 /app/data/history/{ts}.json 元数据。"""
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
    """返回标准时间戳字符串 YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
