"""add system_prompt to ai_model_configs

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-23 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('ai_model_configs', sa.Column('system_prompt', sa.Text(), nullable=True))

    default_system_prompt = """你是一个专业的AI应用开发助手，帮助用户创建Streamlit Web应用。

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
- suggest_start: 当你认为需求已经足够明确可以开始制作时设为 true，此时最后一个选项应为"好的，开始制造"
"""

    op.execute(f"""
        UPDATE ai_model_configs
        SET system_prompt = '{default_system_prompt.replace("'", "''")}'
        WHERE system_prompt IS NULL
    """)


def downgrade() -> None:
    op.drop_column('ai_model_configs', 'system_prompt')
