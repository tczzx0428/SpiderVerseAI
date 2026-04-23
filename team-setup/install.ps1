# OpenClaw Team Installer — Windows (PowerShell)
# Usage: irm http://YOUR_PLATFORM_HOST:8080/install.ps1 | iex

$ErrorActionPreference = "Stop"

$API_KEY       = "sk-your-api-key-here"
$BASE_URL      = "http://YOUR_AI_SERVICE_HOST:3006/v1"
$CODEX_MODEL   = "gpt-5.2-codex"
$OPENCLAW_MODEL= "gpt-5.2"
$SETUP_BASE    = "http://YOUR_PLATFORM_HOST:8080"

function ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function log($msg)  { Write-Host "   ·  $msg" -ForegroundColor DarkGray }
function warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }

Write-Host ""
Write-Host "  PulseTeach AI 团队环境安装" -ForegroundColor White
Write-Host ""

# ── Node.js ───────────────────────────────────────────────────────────────────
function Install-Node {
  log "从内网下载 Node.js 安装包..."
  $nodeMsi = "$env:TEMP\node-lts.msi"
  Invoke-WebRequest -Uri "$SETUP_BASE/node-lts-x64.msi" -OutFile $nodeMsi
  log "安装中..."
  Start-Process msiexec.exe -Wait -ArgumentList "/i `"$nodeMsi`" /quiet /norestart"
  Remove-Item $nodeMsi -Force
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
              [System.Environment]::GetEnvironmentVariable("Path","User")
}

if (Get-Command node -ErrorAction SilentlyContinue) {
  $nodeVer = (node --version).TrimStart('v')
  $nodeMajor = [int]($nodeVer.Split('.')[0])
  if ($nodeMajor -ge 18) { ok "Node.js v$nodeVer" }
  else { warn "Node.js v$nodeVer 版本太低，升级中..."; Install-Node }
} else {
  log "未检测到 Node.js，安装中..."; Install-Node
}
ok "npm $(npm --version)"

# ── Codex CLI ─────────────────────────────────────────────────────────────────
log "安装 Codex CLI..."
npm install -g @openai/codex --silent
ok "Codex CLI 安装完成"

# ── Codex 配置 ────────────────────────────────────────────────────────────────
$codexDir = "$env:USERPROFILE\.codex"
New-Item -ItemType Directory -Force -Path $codexDir | Out-Null

@"
{"OPENAI_API_KEY": "$API_KEY"}
"@ | Set-Content -Path "$codexDir\auth.json" -Encoding UTF8

@"
model_provider = "team"
model = "$CODEX_MODEL"
model_reasoning_effort = "high"
disable_response_storage = true
preferred_auth_method = "apikey"

[model_providers.team]
name = "team"
base_url = "$BASE_URL"
wire_api = "responses"
"@ | Set-Content -Path "$codexDir\config.toml" -Encoding UTF8

ok "Codex 配置完成"

# ── OpenClaw ──────────────────────────────────────────────────────────────────
log "安装 OpenClaw..."
npm install -g openclaw --silent
ok "OpenClaw 安装完成"

# ── OpenClaw 配置 ─────────────────────────────────────────────────────────────
$oclawDir = "$env:USERPROFILE\.openclaw"
New-Item -ItemType Directory -Force -Path $oclawDir | Out-Null

if (-Not (Test-Path "$oclawDir\openclaw.json")) {
  $workspace = "$oclawDir\workspace" -replace '\\', '\\'
  @"
{
  "models": {
    "mode": "merge",
    "providers": {
      "team": {
        "baseUrl": "$BASE_URL",
        "apiKey": "$API_KEY",
        "api": "openai-completions",
        "models": [
          {
            "id": "$OPENCLAW_MODEL",
            "name": "GPT-5.2 (Team)",
            "contextWindow": 1000000,
            "maxTokens": 16000,
            "reasoning": false,
            "input": ["text"],
            "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": { "primary": "team/$OPENCLAW_MODEL" },
      "workspace": "$workspace",
      "compaction": { "mode": "safeguard" }
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": { "mode": "token" }
  }
}
"@ | Set-Content -Path "$oclawDir\openclaw.json" -Encoding UTF8
  ok "OpenClaw 配置写入完成"
} else {
  ok "OpenClaw 已有配置，跳过"
}

# ── Gateway ───────────────────────────────────────────────────────────────────
log "启动 OpenClaw Gateway..."
try { openclaw gateway install 2>$null } catch {}
try { openclaw gateway start   2>$null } catch {}

$started = $false
for ($i = 1; $i -le 5; $i++) {
  Start-Sleep 1
  try {
    $status = openclaw gateway status 2>$null
    if ($status -match "running") { ok "Gateway 已启动"; $started = $true; break }
  } catch {}
}
if (-Not $started) {
  warn "Gateway 可能还在启动，稍后运行 'openclaw gateway status' 确认"
}

# ── PulseTeach AI CLI ──────────────────────────────────────────────────────────
log "安装 PulseTeach AI CLI..."
$peBinDir = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $peBinDir | Out-Null
$peScript = "$peBinDir\pe"
$ptScript = "$peBinDir\pt"
try {
  Invoke-WebRequest -Uri "$SETUP_BASE/pe" -OutFile $peScript
  Copy-Item $peScript $ptScript -Force
  ok "pt CLI 已下载到 $ptScript"
} catch {
  warn "pt CLI 下载失败，请稍后手动安装"
}

# 确保 PATH 包含 ~/.local/bin
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$peBinDir*") {
  [System.Environment]::SetEnvironmentVariable("Path", "$peBinDir;$userPath", "User")
  $env:Path = "$peBinDir;$env:Path"
  ok "已将 $peBinDir 加入 PATH"
}

# 安装 requests 依赖
try { python -m pip install requests -q 2>$null } catch {}
try { python3 -m pip install requests -q 2>$null } catch {}
ok "pt CLI 依赖已安装"

# ── PulseTeach AI 登录 ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  登录 PulseTeach AI 平台  (http://YOUR_PLATFORM_HOST)" -ForegroundColor White
Write-Host "  账号格式：姓名全拼，密码：全拼+123"
Write-Host ""
try {
  python $ptScript login --url "http://YOUR_PLATFORM_HOST"
} catch {
  warn "PulseTeach AI 登录失败，请稍后运行: pt login --url http://YOUR_PLATFORM_HOST"
}

# ── 安装 PulseTeach AI Skill ───────────────────────────────────────────────────
$skillDir = "$env:USERPROFILE\.openclaw\workspace\skills\pt-space"
if (-Not (Test-Path $skillDir)) {
  New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
  try {
    Invoke-WebRequest -Uri "$SETUP_BASE/pt-space-skill.md" -OutFile "$skillDir\SKILL.md"
    ok "PulseTeach AI Skill 已安装"
  } catch {
    warn "PulseTeach AI Skill 下载失败"
  }
}

# ── 交给 Codex 接管验证 ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  脚本完成，启动 AI 助手进行验证..." -ForegroundColor White
Write-Host ""

$tmpSetup = "$env:TEMP\openclaw-setup.md"
try {
  Invoke-WebRequest -Uri "$SETUP_BASE/SETUP.md" -OutFile $tmpSetup
  $setupContent = Get-Content $tmpSetup -Raw
  codex "请读取以下安装指南并执行验证：$setupContent"
} catch {
  codex "环境安装完成，请验证 Node.js、Codex、OpenClaw、pt 命令均正常，有问题自动修复，中文沟通。"
}
