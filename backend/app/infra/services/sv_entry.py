"""SpiderVerseAI 平台入口 - 自动注入到每个应用容器中。
功能:
1. 提取当前用户标识（sv_user 参数）
2. 代理执行用户的 app_original.py
"""
import streamlit as st
import runpy

# ── 1. 用户标识 ──────────────────────────────────────
_user = st.query_params.get("sv_user", "anonymous")


# ── 2. 代理执行用户应用 ──────────────────────────────
runpy.run_path("/app/app_original.py", run_name="__main__")
