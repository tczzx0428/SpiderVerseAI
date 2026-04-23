import { Form, Input } from "antd";
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

function NeuralBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let nodes: Array<{ x: number; y: number; vx: number; vy: number; size: number }> = [];
    let mouse = { x: -1000, y: -1000 };

    const resize = () => {
      canvas.width = window.innerWidth * 2;
      canvas.height = window.innerHeight * 2;
      ctx.scale(2, 2);
    };

    const init = () => {
      resize();
      const w = window.innerWidth;
      const h = window.innerHeight;
      nodes = Array.from({ length: 45 }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 2 + 1,
      }));
    };

    const draw = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;

      ctx.fillStyle = "rgba(10,10,15,0.15)";
      ctx.fillRect(0, 0, w, h);

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        const dx = mouse.x - n.x;
        const dy = mouse.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200) {
          n.vx += (dx / dist) * 0.02;
          n.vy += (dy / dist) * 0.02;
        }

        n.vx *= 0.99; n.vy *= 0.99;
        n.x += n.vx; n.y += n.vy;

        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.size, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(139,92,246,0.6)";
        ctx.fill();

        for (let j = i + 1; j < nodes.length; j++) {
          const m = nodes[j];
          const ddx = n.x - m.x; const ddy = n.y - m.y;
          const d = ddx * ddx + ddy * ddy;
          if (d < 18000) {
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(m.x, m.y);
            const alpha = 0.12 * (1 - d / 18000);
            ctx.strokeStyle = `rgba(139,92,246,${alpha})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(draw);
    };

    init();
    draw();

    const onMove = (e: MouseEvent | TouchEvent) => {
      const ev = "touches" in e ? e.touches[0] : e;
      mouse.x = ev.clientX; mouse.y = ev.clientY;
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("touchmove", onMove);
    window.addEventListener("resize", init);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("touchmove", onMove);
      window.removeEventListener("resize", init);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ position: "fixed", inset: 0, width: "100%", height: "100%", zIndex: 0 }}
    />
  );
}

export default function LoginPageV2() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form] = Form.useForm();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true); setError("");
    try {
      const res = await login(values.username, values.password);
      setAuth(res.data.user, res.data.access_token);
      navigate("/");
    } catch (e: any) {
      setError(e.response?.data?.detail || "用户名或密码错误");
    } finally { setLoading(false); }
  };

  return (
    <div style={{
      minHeight: "100vh",
      fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'SF Pro', 'PingFang SC', sans-serif",
      position: "relative", display: "flex", alignItems: "center", justifyContent: "center",
      background: "#0a0a0f",
    }}>
      <NeuralBackground />

      {/* 主卡片 */}
      <div style={{
        position: "relative", zIndex: 1,
        width: 440,
        background: "rgba(20,20,28,0.75)",
        backdropFilter: "blur(40px)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 24,
        padding: "48px 44px",
        boxShadow: "0 25px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.03) inset",
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12, marginBottom: 36 }}>
          <div style={{
            width: 42, height: 42, background: "linear-gradient(135deg,#8b5cf6,#6366f1)",
            borderRadius: 11, display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16, fontWeight: 800, color: "#fff", letterSpacing: "-0.5px",
            boxShadow: "0 8px 24px rgba(139,92,246,0.35)",
          }}>PT</div>
          <div>
            <div style={{ fontSize: 19, fontWeight: 700, color: "#fff", letterSpacing: "-0.3px" }}>PulseTeach AI</div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 1 }}>律动课堂</div>
          </div>
        </div>

        {/* 标题 */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <h1 style={{ fontSize: 26, fontWeight: 700, color: "#fff", margin: "0 0 8px", letterSpacing: "-0.5px" }}>
            律动课堂，让教学灵感不打烊。
          </h1>
          <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", margin: 0, lineHeight: 1.7 }}>
            在这里，AI 守护你的教育初心，让创意不再被繁琐的流程困住。<br />
            一句自然语言，AI 帮你完成「构建 → 部署 → 上线」全流程。<br />
            零代码，也能打造惊艳的互动教学工具，让课堂节奏随心掌控。
          </p>
        </div>

        {error && (
          <div style={{
            background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10,
            padding: "10px 14px", fontSize: 13, color: "#f87171", marginBottom: 22, textAlign: "center",
          }}>{error}</div>
        )}

        <Form form={form} onFinish={handleLogin} layout="vertical" requiredMark={false}>
          <Form.Item name="username" label={<span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.7)" }}>用户名</span>}
            rules={[{ required: true, message: "请输入用户名" }]} style={{ marginBottom: 18 }}>
            <Input size="large" placeholder="请输入用户名"
              style={{
                borderRadius: 10, background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)", fontSize: 14, padding: "10px 14px",
                color: "#fff",
              }} />
          </Form.Item>

          <Form.Item name="password" label={<span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.7)" }}>密码</span>}
            rules={[{ required: true, message: "请输入密码" }]} style={{ marginBottom: 30 }}>
            <Input.Password size="large" placeholder="请输入密码"
              style={{
                borderRadius: 10, background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)", fontSize: 14, padding: "10px 14px",
                color: "#fff",
              }} />
          </Form.Item>

          <button type="submit" disabled={loading} style={{
            width: "100%", padding: "13px 0",
            background: loading ? "#3d3d50" : "linear-gradient(135deg,#8b5cf6,#6366f1)",
            color: "#fff", border: "none", borderRadius: 12,
            fontSize: 15, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
            transition: "all 0.3s", boxShadow: loading ? "none" : "0 8px 28px rgba(139,92,246,0.35)",
          }}>{loading ? "登录中..." : "登 录"}</button>
        </Form>

        {/* 底部特性 */}
        <div style={{
          display: "flex", justifyContent: "center", gap: 24, marginTop: 28,
          paddingTop: 24, borderTop: "1px solid rgba(255,255,255,0.06)",
        }}>
          {[{ icon: "⚡", text: "秒级生成" }, { icon: "🚀", text: "自动部署" }, { icon: "🤖", text: "AI 驱动" }].map((item) => (
            <div key={item.text} style={{ textAlign: "center" }}>
              <div style={{ fontSize: 18, marginBottom: 4 }}>{item.icon}</div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", fontWeight: 500 }}>{item.text}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
