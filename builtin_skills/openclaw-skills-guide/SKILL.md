---
name: openclaw-skills-guide
description: 教 openclaw 如何操作 SpiderVerseAI Skills 市场，搜索、查看和安装 Skills
---

# openclaw Skills 市场操作指南

你可以通过 SpiderVerseAI 的 CLI API 帮助用户管理 Skills。

## API 信息

- 基础地址：`http://localhost:9099`（根据部署地址调整）
- 认证：请求头 `X-CLI-Token: <token>` 或 URL 参数 `?token=<token>`
- 未配置 token 时可直接访问

## 接口

### 1. 搜索 Skills

```bash
curl -s http://localhost:9099/api/cli/skills?q=关键词
```

参数：`?q=` 搜索、`?category=` 过滤（dev-tools / text / data / automation / other）

### 2. 查看详情

```bash
curl -s http://localhost:9099/api/cli/skills/{name}
```

### 3. 安装 Skill

```bash
curl -o /tmp/{name}.zip http://localhost:9099/api/cli/skills/{name}/install \
  && mkdir -p ~/.openclaw/skills \
  && unzip -o /tmp/{name}.zip -d ~/.openclaw/skills/ \
  && rm /tmp/{name}.zip
```

## 流程

当用户要求安装 Skill 时：

1. **搜索** — 调用列表接口查找
2. **确认** — 展示名称、描述、版本，让用户确认
3. **安装** — 下载 zip 解压到 `~/.openclaw/skills/`
4. **验证** — 列出文件，告知完成

当用户问"有什么 Skills"：

1. 调用 `curl -s .../api/cli/skills`
2. 格式化为列表展示

## 注意

- 安装目录固定 `~/.openclaw/skills/`
- 搜索无结果时引导用户去网页端浏览
- 下载会自动计入统计
