import { Form, Input } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

const INSTALL_CMD = `curl -fsSL http://10.104.29.28/install.sh | bash`;

export default function LoginPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [form] = Form.useForm();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    setError("");
    try {
      const res = await login(values.username, values.password);
      setAuth(res.data.user, res.data.access_token);
      navigate("/");
    } catch (e: any) {
      setError(e.response?.data?.detail || "用户名或密码错误");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(INSTALL_CMD);
      } else {
        const el = document.createElement("textarea");
        el.value = INSTALL_CMD;
        el.style.position = "fixed";
        el.style.left = "-9999px";
        document.body.appendChild(el);
        el.select();
        document.execCommand("copy");
        document.body.removeChild(el);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'SF Pro', 'PingFang SC', sans-serif",
    }}>
      {/* ── 左侧深色面板 ── */}
      <div style={{
        width: "50%",
        background: "#111",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "60px 64px",
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 48 }}>
          <div style={{
            width: 44, height: 44, background: "#fff", borderRadius: 10,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16, fontWeight: 700, color: "#111", letterSpacing: "-0.5px",
            flexShrink: 0,
          }}>SV</div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#fff", letterSpacing: "-0.3px" }}>SpiderVerseAI</div>
            <div style={{ fontSize: 12, color: "#555", marginTop: 1 }}>灵感宇宙 · AI 创作平台</div>
          </div>
        </div>

        {/* 标题 */}
        <div style={{ marginBottom: 48 }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, color: "#fff", letterSpacing: "-1px", margin: "0 0 12px", lineHeight: 1.2 }}>
            释放灵感<br />创造无限可能
          </h1>
          <p style={{ fontSize: 14, color: "#555", margin: 0, lineHeight: 1.7 }}>
            用 AI 的力量，将灵感转化为现实。<br />
            探索无限创意宇宙，让每一个灵感都闪耀。
          </p>
        </div>

        {/* 安装命令块 */}
        <div>
          <div style={{ fontSize: 12, color: "#444", marginBottom: 10, fontWeight: 500, letterSpacing: "0.5px", textTransform: "uppercase" }}>
            一键安装开发环境
          </div>
          <div style={{
            background: "#1a1a1a",
            border: "1px solid #2a2a2a",
            borderRadius: 10,
            padding: "14px 16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
          }}>
            <code style={{ fontSize: 13, color: "#a3e635", fontFamily: "'SF Mono', 'Fira Code', monospace", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {INSTALL_CMD}
            </code>
            <button
              onClick={handleCopy}
              style={{
                flexShrink: 0,
                padding: "5px 12px",
                background: copied ? "#22c55e" : "#2a2a2a",
                color: copied ? "#fff" : "#888",
                border: `1px solid ${copied ? "#22c55e" : "#333"}`,
                borderRadius: 6,
                fontSize: 12,
                fontWeight: 500,
                cursor: "pointer",
                transition: "all 0.2s",
                whiteSpace: "nowrap",
              }}
            >
              {copied ? "已复制 ✓" : "复制"}
            </button>
          </div>
          <p style={{ fontSize: 12, color: "#333", marginTop: 10, margin: "10px 0 0" }}>
            在终端运行，自动安装 Codex / OpenClaw / sv CLI
          </p>
        </div>
      </div>

      {/* ── 右侧白色面板 ── */}
      <div style={{
        width: "50%",
        background: "#fff",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px 64px",
      }}>
        <div style={{ width: "100%", maxWidth: 360 }}>
          <div style={{ marginBottom: 36 }}>
            <h2 style={{ fontSize: 24, fontWeight: 700, color: "#1a1a1a", letterSpacing: "-0.5px", margin: "0 0 6px" }}>
              欢迎登录
            </h2>
            <p style={{ fontSize: 13, color: "#999", margin: 0 }}>
              账号格式：姓名全拼 &nbsp;·&nbsp; 密码：全拼 + 123
            </p>
          </div>

          {error && (
            <div style={{
              background: "#fff1f0", border: "1px solid #fecaca",
              borderRadius: 8, padding: "10px 14px",
              fontSize: 13, color: "#ef4444", marginBottom: 20,
            }}>
              {error}
            </div>
          )}

          <Form form={form} onFinish={handleLogin} layout="vertical" requiredMark={false}>
            <Form.Item
              name="username"
              label={<span style={{ fontSize: 13, fontWeight: 500, color: "#1a1a1a" }}>用户名</span>}
              rules={[{ required: true, message: "请输入用户名" }]}
              style={{ marginBottom: 16 }}
            >
              <Input
                size="large"
                placeholder="请输入用户名"
                style={{ borderRadius: 8, border: "1px solid #e5e5e5", fontSize: 14 }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span style={{ fontSize: 13, fontWeight: 500, color: "#1a1a1a" }}>密码</span>}
              rules={[{ required: true, message: "请输入密码" }]}
              style={{ marginBottom: 28 }}
            >
              <Input.Password
                size="large"
                placeholder="请输入密码"
                style={{ borderRadius: 8, border: "1px solid #e5e5e5", fontSize: 14 }}
              />
            </Form.Item>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%", padding: "13px 0",
                background: loading ? "#666" : "#1a1a1a",
                color: "#fff", border: "none", borderRadius: 8,
                fontSize: 15, fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                transition: "background 0.2s",
              }}
            >
              {loading ? "登录中..." : "登录"}
            </button>
          </Form>
        </div>
      </div>
    </div>
  );
}
