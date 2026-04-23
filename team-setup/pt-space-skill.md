# PulseTeach AI Skill — 需求到上线全流程

你是一个 AI 工程助手，能够帮助用户将需求转化为可运行的 Streamlit 应用并部署到 PulseTeach AI 平台。

---

## 什么时候使用这个 Skill

用户说类似以下内容时启动：
- "帮我做一个 xxx 工具"
- "部署 xxx 应用"
- "我需要一个 xxx 功能"
- "上线一个 xxx"
- "pt deploy" / "发布应用"

---

## 完整工作流程

### 第一步：理解需求

和用户确认：
1. **应用名称**（用于目录名和平台标识，英文小写，如 `text-cleaner`）
2. **功能描述**（做什么，输入什么，输出什么）
3. **需要哪些 Python 库**（如有特殊需求）

### 第二步：获取代码规范

在生成代码前，先获取平台的代码规范 Prompt：

```bash
pt rules
```

这会输出平台管理员设定的代码规范，**必须严格遵守**，包括：
- Streamlit 应用结构要求
- 历史记录保存方式（run_id/username/timestamp/inputs/summary/output_files 格式）
- 路径规范（DATA_DIR 自适应写法）
- 禁止事项（calamine、Windows 专用包、硬编码路径等）
- 其他团队约定

### 第三步：生成代码（用 Codex）

在以下目录创建项目（如果不存在则新建）：
```
~/Desktop/pt-apps/{应用名}/
```

在该目录启动 Codex，告知：
1. 代码规范（来自 pt rules 的输出）
2. 用户需求
3. 需要生成：`app.py` + `requirements.txt`（复杂工具还需 `config.py` + `src/`）

**app.py 核心要求：**
- `st.set_page_config(...)` 必须是第一行
- DATA_DIR 使用自适应写法：`Path("/app/data") if Path("/app").exists() else BASE_DIR / "data"`
- 有运行结果时写入 HISTORY_DIR，格式包含 run_id/username/timestamp/inputs/summary/output_files
- 所有异常用 try-except + st.error() 处理，不暴露 Traceback

**requirements.txt 要求：**
- 每行一个包名，版本用 >=
- 不包含标准库
- 禁止使用 calamine（Excel 用 openpyxl）

### 第四步：部署到 PulseTeach AI

代码写好后，在项目目录执行：

```bash
cd ~/Desktop/pe-apps/{应用名}
pt deploy --name "{应用名称}" --slug {slug} --desc "{一句话描述}"
```

> **注意**：小龙虾已知应用名称和 slug（在第一步和用户确认过），直接传入参数，无需交互输入。

`pt deploy` 会自动：
1. 将目录打包为 zip（忽略 .git、__pycache__ 等）
2. 上传到平台
3. 构建 Docker 镜像
4. 启动容器并配置路由
5. 返回访问链接

**首次部署**：通过 `--name`、`--slug`、`--desc` 直接传入参数，跳过交互提示。
**后续更新**：再次运行 `pt deploy` 即可，会自动识别已有应用（无需重复传参）。

### 第五步：告知用户结果

部署成功后，告知用户：
- 应用访问链接（如 `http://YOUR_PLATFORM_HOST/apps/text-cleaner/`）
- 需要登录 PulseTeach AI 账号才能访问

---

## 常用 pt 命令速查

```bash
# 账号
pt login              # 登录平台
pt whoami             # 查看当前登录状态
pt status             # 快速检查平台连通性和 token 有效性

# 应用管理
pt list               # 查看所有应用（running 状态显示 URL）
pt deploy --name "{名称}" --slug {slug} --desc "{描述}"  # 首次部署（带参数，无需交互）
pt deploy             # 更新已有应用（再次部署）
pt info {slug}        # 查看应用详情
pt logs {slug}        # 查看构建/运行日志
pt stop {slug}        # 停止应用
pt restart {slug}     # 重启应用
pt delete {slug}      # 删除应用（需确认）
pe open {slug}        # 在浏览器打开应用

# 应用历史
pt history            # 查看所有应用的最近运行记录（全局）
pt history {slug}     # 查看指定应用的运行历史

# 文件
pt files list         # 列出所有应用的历史输出文件
pt files list {slug}  # 列出指定应用的历史输出文件
pt files download {slug} {filepath}  # 下载文件到当前目录

# 规范
pt rules              # 查看代码规范 Prompt（生成代码前必须先看）
pt rules edit         # 在编辑器中修改规范（管理员）
pt rules update --file {file}  # 从文件更新规范（管理员）

# 统计（管理员）
pt stats              # 查看使用统计

# 用户管理（管理员）
pt users list
pt users create --username {u} --password {p} --role user
pt users batch --project {name} --count {n} --password {pw}
pt users reset-pw {id|username} {新密码}
pt users toggle {id|username}   # 启用/禁用
pt users delete {id|username}   # 删除用户（需确认）

# Prompt 模板
pt prompts list
pt prompts get {id}   # 查看完整内容
pt prompts update {id} --title {t} --content {c}
```

---

## 故障排除

**部署失败 / 构建错误：**
```bash
pt logs {slug}
```
常见原因：requirements.txt 包名不存在、app.py 语法错误、依赖冲突

**应用无法访问（401）：**
- `pt whoami` 检查登录状态
- `pt info {slug}` 查看应用状态
- `pt restart {slug}` 重启应用

**pt 命令找不到：**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## 注意事项

1. 代码中**不要**硬编码敏感信息（API key 放 config.py，config.py 不提交 git）
2. 应用目录放在 `~/Desktop/pe-apps/` 下
3. Slug 一旦设定不可更改（需删除重建）
4. 生成代码前**必须**先运行 `pt rules` 获取最新规范
