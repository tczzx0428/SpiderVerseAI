from __future__ import annotations
from typing import Optional

from openai import OpenAI
from app.infra.db.database import SessionLocal
from app.infra.db.repos.ai_model_config_repo import AIModelConfigRepo
from app.config import settings


SYSTEM_PROMPT = """你是一个专业的AI应用开发助手，帮助用户创建Streamlit Web应用。

你的任务是：
1. 通过对话了解用户想要创建什么应用
2. 引导用户明确需求（输入、输出、功能）
3. 当需求足够清晰时，询问用户是否开始制作

## ⚠️ 回复格式要求（必须严格遵守）

每次回复必须使用以下JSON格式，不要输出任何其他内容：

{
  "content": "你的回复正文，用中文友好地回答用户的问题或引导需求",
  "options": ["选项1文字", "选项2文字", "选项3文字"],
  "suggest_start": false
}

### 字段说明：
- content: 你的回复正文，要专业、友好、有引导性
- options: 必须提供3个选项供用户快速选择（如：不同功能方向、确认/补充信息等）
- suggest_start: 当你认为需求已经足够明确可以开始制作时设为 true，此时最后一个选项应为"好的，开始制作"

### 选项设计原则：
1. 选项应该是用户最可能想说的3个方向
2. 选项要简短、具体、可操作
3. 随着对话深入，逐步细化选项
4. 前期选项侧重于探索需求（如"我想做个数据处理工具"、"我需要AI分析功能"等）
5. 后期选项侧重于确认细节（如"就这样开始制作吧"、"我再补充一下"等）

### 对话引导策略：
- 第1-2轮：了解用户想做什麼类型的应用
- 第3-4轮：深入了解输入、处理逻辑、输出格式
- 第5轮+：确认细节，当信息足够时 suggest_start=true
- 每次都要根据当前对话进度给出合适的3个选项

你可以帮助用户创建的应用类型：
- 数据处理工具（Excel/CSV处理、数据清洗、报表生成）
- AI工具（批量调用大模型API、内容生成、文本分析）
- 可视化仪表盘（数据展示、图表分析）
- 表单/问卷工具（数据收集、自动汇总）
- 其他Streamlit Web应用"""


class AIChatService:
    def __init__(self) -> None:
        self._clients: dict[str, OpenAI] = {}

    def _get_model_config(self, usage: str = "chat"):
        db = SessionLocal()
        try:
            repo = AIModelConfigRepo(db)
            config = repo.get_first_for_usage(usage)
            if config and config.api_key:
                return config
        finally:
            db.close()

        return None

    def _get_client(self, usage: str = "chat") -> tuple[OpenAI, str]:
        config = self._get_model_config(usage)

        if config:
            cache_key = f"{config.provider}:{config.model_id}"
            if cache_key not in self._clients or True:
                self._clients[cache_key] = OpenAI(
                    base_url=config.base_url,
                    api_key=config.api_key,
                )
            return self._clients[cache_key], config.model_id

        base_url = settings.ai_base_url or settings.team_base_url or "https://api.openai.com/v1"
        api_key = settings.ai_api_key or settings.team_api_key or ""
        model = settings.ai_model or "gpt-4o-mini"

        if not api_key:
            raise ValueError("未配置AI API Key，请联系管理员在「模型配置」中设置")

        if "default" not in self._clients:
            self._clients["default"] = OpenAI(base_url=base_url, api_key=api_key)

        return self._clients["default"], model

    def chat(self, conversation: list[dict], user_message: str) -> dict:
        client, model = self._get_client("chat")

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

        raw_content = response.choices[0].message.content or ""

        import json, re
        json_match = re.search(r'\{[\s\S]*\}', raw_content)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {
                    "content": parsed.get("content", raw_content),
                    "options": parsed.get("options", []),
                    "suggest_start": parsed.get("suggest_start", False),
                }
            except json.JSONDecodeError:
                pass

        return {
            "content": raw_content,
            "options": [],
            "suggest_start": False,
        }

    def extract_requirements(self, conversation: list[dict]) -> dict:
        client, model = self._get_client("chat")

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
        client, model = self._get_client("code")

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