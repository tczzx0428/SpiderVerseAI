import { Form, Input } from "antd";
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

const INSTALL_CMD = `curl -fsSL http://10.104.29.28/install.sh | bash`;

function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let particles: Array<{
      x: number; y: number; vx: number; vy: number;
      r: number; alpha: number; pulse: number;
    }> = [];

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    const init = () => {
      resize();
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      particles = Array.from({ length: 60 }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 2 + 0.5,
        alpha: Math.random() * 0.5 + 0.1,
        pulse: Math.random() * Math.PI * 2,
      }));
    };

    const draw = () => {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      ctx.clearRect(0, 0, w, h);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.pulse += 0.02;

        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        if (p.y < -10) p.y = h + 10;
        if (p.y > h + 10) p.y = -10;

        const a = p.alpha * (0.5 + 0.5 * Math.sin(p.pulse));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${a})`;
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const dist = dx * dx + dy * dy;
          if (dist < 15000) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = `rgba(255,255,255,${0.06 * (1 - dist / 15000)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(draw);
    };

    init();
    draw();
    window.addEventListener("resize", init);
    return () => { cancelAnimationFrame(animId); window.removeEventListener("resize", init); };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute", inset: 0, width: "100%", height: "100%",
        pointerEvents: "none",
      }}
    />
  );
}

export default function LoginPageV1() {
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
      await navigator.clipboard.writeText(INSTALL_CMD);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex",
      fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'SF Pro', 'PingFang SC', sans-serif",
      overflow: "hidden",
    }}>
      {/* 左侧动态背景面板 */}
      <div style={{
        width: "55%",
        position: "relative",
        background: "linear-gradient(135deg, #0a0a0a 0%, #111827 30%, #0f172a 60%, #0a0a0a 100%)",
        display: "flex", flexDirection: "column", justifyContent: "center",
        padding: "60px 64px", overflow: "hidden",
      }}>
        {/* 动态渐变光晕 */}
        <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
          <div style={{
            position: "absolute", width: 500, height: 500,
            borderRadius: "50%", background: "radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)",
            top: "-10%", left: "-10%", animation: "float1 12s ease-in-out infinite",
          }} />
          <div style={{
            position: "absolute", width: 400, height: 400,
            borderRadius: "50%", background: "radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%)",
            bottom: "-5%", right: "-5%", animation: "float2 15s ease-in-out infinite",
          }} />
          <div style={{
            position: "absolute", width: 300, height: 300,
            borderRadius: "50%", background: "radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)",
            top: "40%", left: "50%", animation: "float3 18s ease-in-out infinite",
          }} />
          <ParticleField />
        </div>

        {/* 内容 */}
        <div style={{ position: "relative", zIndex: 1 }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 48 }}>
            <div style={{
              width: 48, height: 48, background: "#fff", borderRadius: 12,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 17, fontWeight: 800, color: "#0a0a0a", letterSpacing: "-0.5px",
              flexShrink: 0, boxShadow: "0 8px 32px rgba(255,255,255,0.15)",
            }}>PT</div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#fff", letterSpacing: "-0.3px" }}>
                PulseTeach AI
              </div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", marginTop: 2, letterSpacing: "1px" }}>
                律动课堂 · AI 创课平台
              </div>
            </div>
          </div>

          {/* 主标题 */}
          <div style={{ marginBottom: 44 }}>
            <h1 style={{
              fontSize: 40, fontWeight: 800, color: "#fff", letterSpacing: "-1.5px",
              margin: "0 0 18px", lineHeight: 1.12,
            }}>
              律动课堂，让教学灵感不打烊。
            </h1>
            <p style={{ fontSize: 15, color: "rgba(255,255,255,0.5)", margin: 0, lineHeight: 1.85, maxWidth: 400 }}>
              在这里，AI 守护你的教育初心，让创意不再被繁琐的流程困住。<br />
              一句自然语言，AI 帮你完成
              <span style={{ color: "rgba(167,139,250,0.75)" }}>「构建 → 部署 → 上线」</span>
              全流程。<br />
              零代码，也能打造惊艳的互动教学工具，让课堂节奏随心掌控。
            </p>
          </div>

          {/* 特性标签 */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 36 }}>
            {[
              { label: "✦ 零代码，自然语言驱动", highlight: false },
              { label: "⚡ AI 秒级构建课件", highlight: true },
              { label: "🚀 一键部署到课堂", highlight: false },
            ].map((item) => (
              <span key={item.label} style={{
                padding: "6px 14px", borderRadius: 20, fontSize: 12, fontWeight: 500,
                border: item.highlight ? "1px solid rgba(139,92,246,0.3)" : "1px solid rgba(255,255,255,0.12)",
                color: item.highlight ? "rgba(196,181,253,0.9)" : "rgba(255,255,255,0.55)",
                backdropFilter: "blur(10px)",
                background: item.highlight ? "rgba(139,92,246,0.08)" : "rgba(255,255,255,0.04)",
              }}>{item.label}</span>
            ))}
          </div>

          {/* 安装命令块 */}
          <div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginBottom: 10, fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase" }}>
              Quick Install
            </div>
            <div style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 12, padding: "14px 16px",
              display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12,
              backdropFilter: "blur(20px)",
            }}>
              <code style={{
                fontSize: 13, color: "#86efac",
                fontFamily: "'SF Mono','Fira Code','Cascadia Code',monospace",
                whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
              }}>{INSTALL_CMD}</code>
              <button onClick={handleCopy} style={{
                flexShrink: 0, padding: "6px 14px",
                background: copied ? "rgba(34,197,94,0.9)" : "rgba(255,255,255,0.08)",
                color: copied ? "#fff" : "rgba(255,255,255,0.5)",
                border: copied ? "1px solid #22c55e" : "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer",
                transition: "all 0.25s", whiteSpace: "nowrap",
              }}>{copied ? "已复制 ✓" : "复制"}</button>
            </div>
          </div>
        </div>

        <style>{`
          @keyframes float1 { 0%,100%{transform:translate(0,0)} 33%{transform:translate(40px,-20px)} 66%{transform:translate(-20px,30px)} }
          @keyframes float2 { 0%,100%{transform:translate(0,0)} 33%{transform:translate(-30px,25px)} 66%{transform:translate(20px,-15px)} }
          @keyframes float3 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,-30px)} }
        `}</style>
      </div>

      {/* 右侧白色面板 */}
      <div style={{
        width: "45%", background: "#fff",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: "60px 56px",
      }}>
        <div style={{ width: "100%", maxWidth: 360 }}>
          <div style={{ marginBottom: 40 }}>
            <h2 style={{ fontSize: 26, fontWeight: 700, color: "#0a0a0a", letterSpacing: "-0.5px", margin: "0 0 8px" }}>
              欢迎回来
            </h2>
            <p style={{ fontSize: 13, color: "#999", margin: 0 }}>
              登录后开始打造你的互动教学工具
            </p>
          </div>

          {error && (
            <div style={{
              background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10,
              padding: "11px 14px", fontSize: 13, color: "#dc2626", marginBottom: 22,
            }}>{error}</div>
          )}

          <Form form={form} onFinish={handleLogin} layout="vertical" requiredMark={false}>
            <Form.Item name="username" label={<span style={{ fontSize: 13, fontWeight: 600, color: "#333" }}>用户名</span>}
              rules={[{ required: true, message: "请输入用户名" }]} style={{ marginBottom: 18 }}>
              <Input size="large" placeholder="请输入用户名"
                style={{ borderRadius: 10, border: "1.5px solid #e5e7eb", fontSize: 14, padding: "10px 14px" }}
              />
            </Form.Item>
            <Form.Item name="password" label={<span style={{ fontSize: 13, fontWeight: 600, color: "#333" }}>密码</span>}
              rules={[{ required: true, message: "请输入密码" }]} style={{ marginBottom: 32 }}>
              <Input.Password size="large" placeholder="请输入密码"
                style={{ borderRadius: 10, border: "1.5px solid #e5e7eb", fontSize: 14, padding: "10px 14px" }}
              />
            </Form.Item>
            <button type="submit" disabled={loading} style={{
              width: "100%", padding: "14px 0",
              background: loading ? "#9ca3af" : "#0a0a0a", color: "#fff",
              border: "none", borderRadius: 10, fontSize: 15, fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer", transition: "all 0.25s",
              boxShadow: loading ? "none" : "0 4px 16px rgba(0,0,0,0.2)",
            }}>{loading ? "登录中..." : "登 录"}</button>
          </Form>
        </div>
      </div>
    </div>
  );
}
