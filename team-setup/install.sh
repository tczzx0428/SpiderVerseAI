#!/usr/bin/env bash
# OpenClaw + Codex + PE Space 团队一键安装
# 用法: curl -fsSL http://172.26.88.170:8080/install.sh | bash

set -euo pipefail

RESET="\033[0m"; BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; DIM="\033[2m"
ok()   { printf "  ${GREEN}✓${RESET} %s\n" "$*"; }
log()  { printf "  ${DIM}·${RESET} %s\n" "$*"; }
warn() { printf "  ${YELLOW}⚠${RESET}  %s\n" "$*"; }

SETUP_BASE="http://172.26.88.170:8080"

printf "\n  ${BOLD}PE Space 团队环境安装${RESET}\n\n"

# ── Node.js ───────────────────────────────────────────────────────────────────
install_node() {
  log "从内网下载 Node.js 安装包 ..."
  TMP_PKG="/tmp/node-lts-install.pkg"
  curl -fsSL "${SETUP_BASE}/node-lts.pkg" -o "$TMP_PKG"
  log "安装中（需要管理员密码）..."
  sudo installer -pkg "$TMP_PKG" -target / -verboseR 2>/dev/null
  rm -f "$TMP_PKG"
  # 刷新 PATH
  export PATH="/usr/local/bin:/usr/bin:$PATH"
}

if command -v node &>/dev/null; then
  NODE_MAJOR="$(node --version | sed 's/v//' | cut -d. -f1)"
  if [[ "$NODE_MAJOR" -ge 18 ]]; then ok "Node.js $(node --version)"
  else warn "Node.js 版本太低，重新安装 ..."; install_node; fi
else
  log "未检测到 Node.js，安装中 ..."; install_node
fi
ok "npm $(npm --version)"

# ── Codex CLI ─────────────────────────────────────────────────────────────────
log "安装 Codex CLI ..."
npm install -g @openai/codex --silent 2>/dev/null || sudo npm install -g @openai/codex --silent
ok "Codex CLI $(codex --version 2>/dev/null || echo 'installed')"

# ── OpenClaw ──────────────────────────────────────────────────────────────────
log "安装 OpenClaw ..."
npm install -g openclaw --silent 2>/dev/null || sudo npm install -g openclaw --silent
ok "OpenClaw $(openclaw --version 2>/dev/null || echo 'installed')"

# ── Gateway ───────────────────────────────────────────────────────────────────
log "启动 OpenClaw Gateway ..."
openclaw gateway install 2>/dev/null || true
openclaw gateway start  2>/dev/null || true
for i in 1 2 3 4 5; do
  sleep 1
  if openclaw gateway status 2>/dev/null | grep -q "running"; then
    ok "Gateway 已启动"; break
  fi
  [[ $i -eq 5 ]] && warn "Gateway 稍后运行 'openclaw gateway status' 确认"
done

# ── PE Space CLI ──────────────────────────────────────────────────────────────
log "安装 PE Space CLI ..."
PE_BIN=""
if curl -fsSL "${SETUP_BASE}/pe" -o /usr/local/bin/pe 2>/dev/null && chmod +x /usr/local/bin/pe 2>/dev/null; then
  PE_BIN="/usr/local/bin/pe"
else
  mkdir -p "$HOME/.local/bin"
  curl -fsSL "${SETUP_BASE}/pe" -o "$HOME/.local/bin/pe" && chmod +x "$HOME/.local/bin/pe"
  PE_BIN="$HOME/.local/bin/pe"
  # 确保 PATH 包含 ~/.local/bin
  for rc in ~/.zshrc ~/.bashrc ~/.bash_profile; do
    [[ -f "$rc" ]] && grep -q '\.local/bin' "$rc" && continue
    [[ -f "$rc" ]] && echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
  done
  export PATH="$HOME/.local/bin:$PATH"
fi

# 安装 requests 依赖
python3 -m pip install requests -q 2>/dev/null || pip3 install requests -q 2>/dev/null || true
ok "PE CLI 已安装 ($PE_BIN)"

# ── PE Space 登录 ─────────────────────────────────────────────────────────────
printf "\n  ${BOLD}登录 PE Space 平台${RESET}  (http://120.48.9.224)\n"
printf "  账号格式：姓名全拼，密码：全拼+123\n\n"
pe login --url "http://120.48.9.224"

# ── 安装 PE Space Skill ───────────────────────────────────────────────────────
SKILL_DIR="$HOME/.openclaw/workspace/skills/pe-space"
if [[ ! -d "$SKILL_DIR" ]]; then
  mkdir -p "$SKILL_DIR"
  curl -fsSL "${SETUP_BASE}/pe-space-skill.md" -o "$SKILL_DIR/SKILL.md" 2>/dev/null || true
  ok "PE Space Skill 已安装"
fi

# ── 交给 Codex 接管验证 ────────────────────────────────────────────────────────
printf "\n  ${BOLD}脚本完成，启动 AI 助手进行验证 ...${RESET}\n\n"
TMPSETUP=$(mktemp /tmp/openclaw-setup-XXXX.md)
curl -fsSL "${SETUP_BASE}/SETUP.md" -o "$TMPSETUP" 2>/dev/null || \
  cp "$(dirname "$0")/SETUP.md" "$TMPSETUP" 2>/dev/null || true

if [[ -f "$TMPSETUP" ]]; then
  codex "请读取以下安装指南并执行验证：$(cat "$TMPSETUP")"
else
  codex "环境安装完成，请验证 Node.js、Codex、OpenClaw、pe 命令均正常，有问题自动修复，中文沟通。"
fi
