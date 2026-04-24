from __future__ import annotations
from typing import Optional

from openai import OpenAI
from app.infra.db.database import SessionLocal
from app.infra.db.repos.ai_model_config_repo import AIModelConfigRepo
from app.config import settings


SYSTEM_PROMPT = """你是一个专业的AI应用开发助手，帮助用户创建高质量的Streamlit Web应用。

你的任务是：
1. 通过对话了解用户想要创建什么应用
2. 引导用户明确需求（输入、输出、功能）
3. **评估需求的可行性**，如果需求不符合代码规范或技术限制，要主动告知用户
4. 当需求足够清晰且符合规范时，询问用户是否开始制作

## ⚠️ 回复格式要求（必须严格遵守）

每次回复必须使用以下JSON格式，不要输出任何其他内容：

{
  "content": "你的回复正文，用中文友好地回答用户的问题或引导需求",
  "options": ["选项1文字", "选项2文字", "选项3文字"],
  "suggest_start": false
}

### 字段说明：
- content: 你的回复正文，要专业、友好、有引导性
- options: 必须提供3个选项供用户快速选择
- suggest_start: 当你认为需求已经足够明确**且符合代码规范**时设为 true

## 🔴 代码规范要求（非常重要）

在确认开始制作前，必须确保用户的需求符合以下规范：

### ✅ 允许的应用类型：
1. **数据可视化类**：图表展示、数据报表、科学原理演示动画
2. **实用工具类**：抽奖、排课、计算器、转换器、随机分配器
3. **AI分析类**：文本分析、图像处理、数据智能分析、报告生成
4. **表单收集类**：问卷、调查、报名系统
5. **教育学习类**：知识测验、概念解释、交互式教学

### ❌ 不允许的功能：
1. **禁止任何违法违规内容**：赌博、色情、暴力、侵权等
2. **禁止恶意功能**：爬虫攻击、密码破解、DDoS工具等
3. **禁止过度资源消耗**：无限循环、大量并发请求、大文件处理无限制
4. **禁止不安全操作**：直接执行用户输入的代码、SQL注入风险等
5. **禁止侵犯隐私**：收集敏感个人信息、人脸识别等

### 📋 Streamlit代码质量标准：
1. 使用 `st.` 前缀的所有Streamlit组件
2. 合理使用 `st.columns()` 进行布局
3. 所有函数必须有清晰的注释
4. 用户输入必须做验证和错误处理
5. 使用 `st.session_state` 管理状态
6. 避免硬编码，使用配置变量
7. 响应式设计，适配不同屏幕尺寸
8. 提供清晰的用户引导和使用说明

### ⚠️ 规范检查流程：
当用户提出需求时，你需要：
1. 判断是否属于允许的应用类型
2. 识别潜在的安全或技术问题
3. 如果有问题，主动向用户说明并建议修改方案
4. 确认无误后才能设置 suggest_start=true

### 对话引导策略：
- 第1-2轮：了解用户想做什麼类型的应用
- 第3-4轮：深入了解功能细节，同时检查是否符合规范
- 第5轮+：确认细节，当信息足够且符合规范时 suggest_start=true
- 每次都要根据当前对话进度给出合适的3个选项

### 选项设计原则：
1. 选项应该是用户最可能想说的3个方向
2. 选项要简短、具体、可操作
3. 随着对话深入，逐步细化选项
4. 前期选项侧重于探索需求
5. 后期选项侧重于确认细节或指出需要调整的地方"""


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

    def _get_system_prompt(self) -> str:
        config = self._get_model_config("chat")
        if config and config.system_prompt:
            return config.system_prompt
        return SYSTEM_PROMPT

    def chat(self, conversation: list[dict], user_message: str) -> dict:
        client, model = self._get_client("chat")
        system_prompt = self._get_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
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

        prompt = f"""根据以下需求，生成一个完整、高质量的Streamlit Web应用代码。

## 应用需求
- 名称：{requirements.get('app_name', '新应用')}
- 描述：{requirements.get('app_description', '')}
- 输入：{requirements.get('inputs', [])}
- 处理逻辑：{requirements.get('processing', '')}
- 输出：{requirements.get('outputs', [])}
- 特性：{requirements.get('features', [])}

## 🔴 代码质量规范（必须严格遵守）

### 文件结构
只输出两个文件的内容：app.py 和 requirements.txt

### app.py 规范（非常重要）
1. **第一行必须是** `st.set_page_config(page_title="...", layout="wide")`
2. **使用中文界面**，所有UI文本用中文
3. **页面顶部必须包含**：
   - 应用标题（st.title或st.header）
   - 清晰的功能说明（st.markdown）
   - 使用说明（如果需要）
4. **布局规范**：
   - 使用 `st.columns()` 进行响应式布局
   - 重要操作放在侧边栏 `st.sidebar`
   - 合理使用 `st.container()` 和 `st.expander()`
5. **输入验证**：
   - 所有用户输入必须做类型检查和范围验证
   - 使用 `try-except` 包裹可能出错的操作
   - 错误信息用 `st.error()` 展示
6. **性能优化**：
   - 耗时操作用 `st.spinner()` 包裹
   - 批量操作必须有 `st.progress()`
   - 大数据用 `st.cache_data` 缓存
7. **状态管理**：
   - 使用 `st.session_state` 管理应用状态
   - 初始化检查：`if 'key' not in st.session_state:`
8. **代码风格**：
   - 函数必须有清晰的 docstring 注释
   - 变量命名要有意义
   - 避免硬编码，使用配置变量
   - 单个函数不超过50行

### 禁止事项（违反将导致部署失败）
- ❌ 禁止硬编码 localhost、127.0.0.1 或绝对路径（用 Path(__file__).parent）
- ❌ 禁止使用 calamine 包（Excel 用 openpyxl）
- ❌ 禁止 Windows 专用包
- ❌ 禁止执行用户输入的代码（eval、exec）
- ❌ 禁止无限循环或递归无终止条件
- ❌ 禁止收集敏感个人信息
- ❌ 禁止访问外部API除非明确需求

### requirements.txt 规范
- 必须包含 streamlit>=1.30.0
- 版本号用 >= 而非 ==
- 保持简洁，只列出必要依赖
- 常用依赖示例：pandas, plotly, matplotlib, pillow

### UI/UX 最佳实践
1. 使用 st.metric() 展示关键指标
2. 使用 st.dataframe/st.table 展示数据
3. 图表使用 plotly 或 matplotlib
4. 按钮要有明确的文字说明
5. 提供示例数据或演示功能
6. 成功操作用 st.success() 反馈

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