import { Form, Input } from "antd";
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

function AuroraBackground() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let animId: number;
    let t = 0;

    const draw = () => {
      t += 0.004;
      const hue1 = (Math.sin(t * 0.7) * 30 + 250) % 360;
      const hue2 = (Math.sin(t * 0.5 + 2) * 25 + 200) % 360;
      const x1 = 40 + Math.sin(t * 0.6) * 15;
      const y1 = 20 + Math.cos(t * 0.8) * 10;
      const x2 = 60 + Math.cos(t * 0.5) * 12;
      const y2 = 70 + Math.sin(t * 0.7) * 15;

      el.style.background = `
        radial-gradient(ellipse ${x1}% ${y1}%, hsla(${hue1},70%,50%,0.18) 0%, transparent 55%),
        radial-gradient(ellipse ${x2}% ${y2}%, hsla(${hue2},65%,45%,0.14) 0%, transparent 50%),
        linear-gradient(160deg, #09090b 0%, #111118 40%, #0c0c12 100%)
      `;

      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animId);
  }, []);

  return <div ref={ref} style={{ position: "fixed", inset: 0, zIndex: 0 }} />;
}

function FloatingOrbs() {
  return (
    <div style={{ position: "fixed", inset: 0, overflow: "hidden", pointerEvents: "none", zIndex: 0 }}>
      {[
        { size: 300, top: "5%", left: "10%", dur: "20s", delay: "0s", opacity: 0.08 },
        { size: 200, top: "60%", left: "75%", dur: "16s", delay: "-5s", opacity: 0.06 },
        { size: 150, top: "35%", left: "55%", dur: "24s", delay: "-10s", opacity: 0.05 },
      ].map((orb, i) => (
        <div key={i} style={{
          position: "absolute",
          width: orb.size, height: orb.size,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(139,92,246,${orb.opacity}) 0%, transparent 70%)`,
          top: orb.top, left: orb.left,
          animation: `orbFloat${i + 1} ${orb.dur} ease-in-out infinite`,
          animationDelay: orb.delay,
        }} />
      ))}
      <style>{`
        @keyframes orbFloat1{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(30px,-20px) scale(1.1)}66%{transform:translate(-15px,25px) scale(0.95)}}
        @keyframes orbFloat2{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-25px,-30px) scale(1.08)}}
        @keyframes orbFloat3{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(20px,15px) scale(1.05)}66%{transform:translate(-20px,-10px) scale(0.97)}
      `}</style>
    </div>
  );
}

export default function LoginPageV3() {
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
      display: "flex", alignItems: "center", justifyContent: "center",
      position: "relative", overflow: "hidden",
    }}>
      <AuroraBackground />
      <FloatingOrbs />

      {/* 登录卡片 */}
      <div style={{
        position: "relative", zIndex: 1,
        width: 420,
        background: "rgba(255,255,255,0.03)",
        backdropFilter: "blur(48px)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 28,
        padding: "52px 44px",
        boxShadow: "0 32px 100px rgba(0,0,0,0.4), 0 0 80px rgba(139,92,246,0.06)",
      }}>
        {/* Logo 区域 */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
            <div style={{
              width: 46, height: 46, background: "#fff", borderRadius: 13,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 17, fontWeight: 800, color: "#0a0a0a", letterSpacing: "-0.5px",
              boxShadow: "0 8px 28px rgba(255,255,255,0.2)",
            }}>SV</div>
            <div style={{ textAlign: "left" }}>
              <div style={{ fontSize: 21, fontWeight: 700, color: "#fff", letterSpacing: "-0.3px" }}>
                SpiderVerseAI
              </div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.38)", marginTop: 1, letterSpacing: "0.5px" }}>
                灵感宇宙 · AI 创作平台
              </div>
            </div>
          </div>

          <h1 style={{
            fontSize: 28, fontWeight: 800, color: "#fff",
            margin: "0 0 10px", letterSpacing: "-0.8px", lineHeight: 1.2,
          }}>
            AI 驱动，一键生成
          </h1>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.42)", margin: 0, lineHeight: 1.7 }}>
            从灵感到产品，只需一句话。<br />AI 自动完成构建、部署、上线全流程。
          </p>
        </div>

        {error && (
          <div style={{
            background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)",
            borderRadius: 12, padding: "11px 16px", fontSize: 13, color: "#fca5a5",
            marginBottom: 22, textAlign: "center",
          }}>{error}</div>
        )}

        <Form form={form} onFinish={handleLogin} layout="vertical" requiredMark={false}>
          <Form.Item name="username"
            label={<span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.6)" }}>用户名</span>}
            rules={[{ required: true, message: "请输入用户名" }]} style={{ marginBottom: 18 }}>
            <Input size="large" placeholder="请输入用户名" style={{
              borderRadius: 12, background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)", fontSize: 14,
              padding: "11px 16px", color: "#fff",
            }} />
          </Form.Item>

          <Form.Item name="password"
            label={<span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.6)" }}>密码</span>}
            rules={[{ required: true, message: "请输入密码" }]} style={{ marginBottom: 32 }}>
            <Input.Password size="large" placeholder="请输入密码" style={{
              borderRadius: 12, background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)", fontSize: 14,
              padding: "11px 16px", color: "#fff",
            }} />
          </Form.Item>

          <button type="submit" disabled={loading} style={{
            width: "100%", padding: "14px 0",
            background: loading ? "rgba(255,255,255,0.15)" : "#fff",
            color: loading ? "rgba(255,255,255,0.4)" : "#0a0a0a",
            border: "none", borderRadius: 14, fontSize: 15, fontWeight: 700,
            cursor: loading ? "not-allowed" : "pointer", transition: "all 0.3s",
            letterSpacing: "0.5px",
          }}>{loading ? "登录中..." : "登 录"}</button>
        </Form>

        {/* 底部特性 */}
        <div style={{
          marginTop: 32, paddingTop: 24,
          borderTop: "1px solid rgba(255,255,255,0.05)",
          display: "flex", justifyContent: "space-around",
        }}>
          {[
            { label: "自然语言描述", sub: "说想法即可" },
            { label: "自动构建部署", sub: "零代码操作" },
            { label: "团队协作管理", sub: "多人共享" },
          ].map((item) => (
            <div key={item.label} style={{ textAlign: "center" }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.7)", marginBottom: 2 }}>{item.label}</div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>{item.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
