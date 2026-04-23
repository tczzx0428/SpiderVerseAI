"""PulseTeach AI 平台入口 - 自动注入到每个应用容器中。
功能:
1. 提取当前用户标识（pt_user 参数）
2. 代理执行用户的 app_original.py
"""
import runpy

import streamlit as st

_user = st.query_params.get("pt_user", "anonymous")
runpy.run_path("/app/app_original.py", run_name="__main__")
