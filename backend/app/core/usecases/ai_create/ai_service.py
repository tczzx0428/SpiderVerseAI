from __future__ import annotations
from typing import Optional

from openai import OpenAI

from app.config import settings


SYSTEM_PROMPT = """你是一个专业的AI应用开发助手，帮助用户创建Streamlit Web应用。

你的任务是：
1. 通过对话了解用户想要创建什么应用
2. 引导用户明确需求（输入、输出、功能）
3. 当需求足够清晰时，告诉用户可以开始生成应用

重要规则：
- 每次回复都要友好、专业
- 主动询问关键信息：应用用途、输入数据格式、处理逻辑、输出形式
- 当用户说"开始"、"生成"、"确认"等词时，表示用户确认了需求
- 不要自己决定"需求已足够"，要等用户确认
- 如果用户的需求不完整，主动追问缺失的信息

你可以帮助用户创建的应用类型：
- 数据处理工具（Excel/CSV处理、数据清洗、报表生成）
- AI工具（批量调用大模型API、内容生成、文本分析）
- 可视化仪表盘（数据展示、图表分析）
- 表单/问卷工具（数据收集、自动汇总）
- 其他Streamlit Web应用"""


class AIChatService:
    def __init__(self) -> None:
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            base_url = settings.ai_base_url or settings.team_base_url or "https://api.openai.com/v1"
            api_key = settings.ai_api_key or settings.team_api_key or ""
            if not api_key:
                raise ValueError("未配置AI API Key，请联系管理员在团队配置中设置")
            self._client = OpenAI(base_url=base_url, api_key=api_key)
        return self._client

    def chat(self, conversation: list[dict], user_message: str) -> str:
        client = self._get_client()
        model = settings.ai_model or "gpt-4o-mini"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation,
            {"role": "user", "content": user_message},
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        return response.choices[0].message.content or ""

    def extract_requirements(self, conversation: list[dict]) -> dict:
        client = self._get_client()
        model = settings.ai_model or "gpt-4o-mini"

        messages = [
            {"role": "system", "content": """根据以下对话，提取用户的应用需求，返回JSON格式。
必须包含以下字段（如果对话中没有提到，使用合理的默认值）：
{
  "app_name": "应用名称",
  "app_description": "应用描述",
  "inputs": ["输入1说明", "输入2说明"],
  "processing": "处理逻辑描述",
  "outputs": ["输出1说明"],
  "features": ["特性1", "特性2"]
}"""},
            *conversation,
            {"role": "user", "content": "请根据以上对话，提取我的应用需求，以JSON格式返回。"},
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )

        import json
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"app_name": "新应用", "app_description": content, "inputs": [], "processing": "", "outputs": [], "features": []}

    def generate_code(self, requirements: dict) -> dict[str, str]:
        client = self._get_client()
        model = settings.ai_code_model or settings.ai_model or "gpt-4o"

        prompt = f"""根据以下需求，生成一个完整的Streamlit Web应用代码。

## 应用需求
- 名称：{requirements.get('app_name', '新应用')}
- 描述：{requirements.get('app_description', '')}
- 输入：{requirements.get('inputs', [])}
- 处理逻辑：{requirements.get('processing', '')}
- 输出：{requirements.get('outputs', [])}
- 特性：{requirements.get('features', [])}

## 技术要求（必须严格遵守）

### 文件结构
只输出两个文件的内容：app.py 和 requirements.txt

### app.py 规范
1. 第一行必须是 st.set_page_config()
2. 使用中文界面
3. 耗时操作用 st.spinner() 包裹
4. 错误用 st.error() 展示
5. 批量操作必须有 st.progress()
6. 页面顶部写清楚工具用途说明

### 禁止事项
- 禁止硬编码 localhost 或 127.0.0.1
- 禁止写死绝对路径，用 Path(__file__).parent
- 禁止使用 calamine 包，Excel 用 openpyxl
- 禁止 Windows 专用包

### requirements.txt 规范
- 必须包含 streamlit>=1.30.0
- 版本号用 >= 而非 ==
- 保持简洁

请直接输出两个文件的完整内容，用 ===APP.PY=== 和 ===REQUIREMENTS.TXT=== 分隔。"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=8000,
        )

        content = response.choices[0].message.content or ""

        parts = content.split("===REQUIREMENTS.TXT===")
        app_py = parts[0].replace("===APP.PY===", "").strip()
        req_txt = parts[1].strip() if len(parts) > 1 else "streamlit>=1.30.0\npandas>=2.0.0"

        return {
            "app.py": app_py,
            "requirements.txt": req_txt,
        }