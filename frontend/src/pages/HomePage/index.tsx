import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listApps, type AppItem } from "@/api/apps";

const TEMPLATES = [
  { icon: "\uD83D\uDD2C", title: "物理原理演示", desc: "光的折射、自由落体、电路模拟、波动干涉等互动实验", prompt: "帮我做一个物理演示网页，展示[具体知识点]，学生可以通过拖拽/点击来观察现象变化，界面简洁适合课堂投影", color: "#3b82f6", bg: "rgba(59,130,246,0.06)" },
  { icon: "\uD83C\uDF0D", title: "地理规律可视化", desc: "气候分布、地形剖面、洋流方向、板块运动等动态地图", prompt: "帮我做一个地理教学网页，用交互式地图展示[具体地理知识]，学生可以点击不同区域查看详情，配色清晰易读", color: "#10b981", bg: "rgba(16,185,129,0.06)" },
  { icon: "\uD83E\uDDE8", title: "趣味数学工具", desc: "函数图像绘制器、概率模拟、几何作图、统计图表生成器", prompt: "帮我做一个数学教学工具，可以[具体功能]，界面友好，适合中小学生操作，支持输入参数实时看到结果变化", color: "#f59e0b", bg: "rgba(245,158,11,0.06)" },
  { icon: "\uD83C\uDFAF", title: "课堂互动游戏", desc: "知识竞答、分组PK、随机点名、计时器、投票器等小工具", prompt: "帮我做一个课堂互动工具，用于[具体场景]，操作简单，一键开始，界面活泼有趣能吸引学生注意力", color: "#ef4444", bg: "rgba(239,68,68,0.06)" },
  { icon: "\uD83D\uDCD6", title: "语文/英语辅助", desc: "古诗词动画、语法树分析、单词记忆卡片、阅读理解助手", prompt: "帮我做一个[学科]教学辅助网页，主题是[具体内容]，图文并茂，有互动元素帮助学生理解", color: "#8b5cf6", bg: "rgba(139,92,246,0.06)" },
  { icon: "\u2697\uFE0F", title: "化学实验模拟", desc: "分子结构3D展示、化学反应动画、周期表互动查询", prompt: "帮我做一个化学教学网页，模拟[具体实验或概念]，安全直观，学生可以看到反应过程的每一步", color: "#06b6d4", bg: "rgba(6,182,212,0.06)" },
];

const STEPS = [
  { num: "1", title: "描述你的想法", desc: "用大白话告诉 AI 你想做什么课件或工具，比如「我想做一个自由落体实验的演示页面」", icon: "\uD83D\uDCAC" },
  { num: "2", title: "AI 自动构建", desc: "平台自动将你的想法转化为完整的互动网页，无需写任何代码", icon: "\u2728" },
  { num: "3", title: "一键部署上线", desc: "生成后直接获得访问链接，打开浏览器就能在课堂上使用", icon: "\uD83D\uDE80" },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [apps, setApps] = useState<AppItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);

  useEffect(() => {
    listApps({ size: 6 }).then((res) => { setApps(res.data.items || []); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="hp-root">
      <style>{`
        .hp-root{font-family:Inter,-apple-system,BlinkMacSystemFont,'SF Pro','PingFang SC',sans-serif;background:#fafbfc;min-height:100%;padding:0 20px}
        .hp-hero{background:linear-gradient(135deg,#0a0a0a 0%,#111827 40%,#1e1b4b 100%);border-radius:24px;margin:20px 0 32px;padding:56px 52px 48px;position:relative;overflow:hidden;color:#fff}
        .hp-hero-glow{position:absolute;inset:0;overflow:hidden;pointer-events:none}
        .hp-hero-glow-1{position:absolute;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(99,102,241,.18) 0%,transparent 70%);top:-15%;right:-5%;animation:hgf1 14s ease-in-out infinite}
        .hp-hero-glow-2{position:absolute;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(139,92,246,.12) 0%,transparent 70%);bottom:-10%;left:10%;animation:hgf2 18s ease-in-out infinite}
        @keyframes hgf1{0%,100%{transform:translate(0,0)}50%{transform:translate(-30px,20px)}}
        @keyframes hgf2{0%,100%{transform:translate(0,0)}50%{transform:translate(25px,-15px)}}
        .hp-badge{display:inline-flex;align-items:center;gap:8px;padding:6px 16px;border-radius:20px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);font-size:13px;font-weight:500;color:rgba(255,255,255,.7);margin-bottom:24px}
        .hp-title{font-size:36px;font-weight:800;letter-spacing:-1px;margin:0 0 16px;line-height:1.35;max-width:580px}
        .hp-title span{background:linear-gradient(135deg,#a78bfa,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .hp-desc{font-size:16px;color:rgba(255,255,255,.55);margin:0 0 32px;line-height:1.85;max-width:520px}
        .hp-btns{display:flex;gap:12px;flex-wrap:wrap}
        .hp-btn-primary{padding:13px 28px;background:#fff;color:#0a0a0a;border:none;border-radius:12px;font-size:15px;font-weight:700;cursor:pointer;transition:all .25s;box-shadow:0 4px 16px rgba(255,255,255,.15)}
        .hp-btn-primary:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(255,255,255,.25)}
        .hp-btn-ghost{padding:13px 28px;background:rgba(255,255,255,.06);color:#fff;border:1px solid rgba(255,255,255,.12);border-radius:12px;font-size:15px;font-weight:600;cursor:pointer;transition:all .25s}
        .hp-btn-ghost:hover{background:rgba(255,255,255,.12)}
        .hp-card{background:#fff;border-radius:18px;padding:28px 24px;border:1px solid #f0f0f0;position:relative;transition:all .25s;cursor:default}
        .hp-card:hover{box-shadow:0 8px 30px rgba(0,0,0,.06);transform:translateY(-2px)}
        .hp-card-icon{width:44px;height:44px;border-radius:14px;background:#f5f5f7;display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:16px}
        .hp-card-num{position:absolute;top:20px;right:20px;width:28px;height:28px;border-radius:50%;color:#fff;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center}
        .hp-card-title{font-size:17px;font-weight:700;color:#1a1a1a;margin:0 0 8px}
        .hp-card-desc{font-size:13.5px;color:#888;margin:0;line-height:1.7}
        .hp-tpl{background:#fff;border-radius:16px;padding:22px 20px;border:1.5px solid #f0f0f0;cursor:pointer;transition:all .25s}
        .hp-tpl:hover{border-color:#e0e0e0;box-shadow:0 4px 16px rgba(0,0,0,.04)}
        .hp-tpl.active{border-color:var(--tpl-color);background:var(--tpl-bg)}
        .hp-tpl-icon{font-size:30px;margin-bottom:12px}
        .hp-tpl-title{font-size:16px;font-weight:700;color:#1a1a1a;margin:0 0 6px}
        .hp-tpl-desc{font-size:13px;color:#888;margin:0;line-height:1.65}
        .hp-tpl-detail{margin-top:14px;padding-top:14px;border-top:1px solid rgba(0,0,0,.06)}
        .hp-tpl-prompt-label{font-size:12px;font-weight:600;color:#666;margin-bottom:8px}
        .hp-tpl-prompt{background:#fff;border-radius:10px;padding:12px 14px;font-size:12.5px;color:#555;line-height:1.7;border:1px solid #eee;font-style:italic}
        .hp-tpl-go{margin-top:12px;width:100%;padding:10px 0;background:var(--tpl-color);color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer}
        .hp-app-card{background:#fff;border-radius:16px;padding:22px;border:1px solid #f0f0f0;cursor:pointer;transition:all .2s}
        .hp-app-card:hover{box-shadow:0 6px 24px rgba(0,0,0,.06);transform:translateY(-2px)}
        .hp-status{padding:3px 10px;border-radius:6px;font-size:11px;font-weight:600}
        .hp-status-running{background:#ecfdf5;color:#059669}
        .hp-status-stopped{background:#fefce8;color:#d97706}
        .hp-status-other{background:#f5f5f5;color:#888}
        .hp-empty{background:#fff;border-radius:18px;padding:52px 32px;text-align:center;border:2px dashed #e5e5e5}
        .hp-tip{background:linear-gradient(135deg,#faf5ff,#f0f4ff);border-radius:18px;padding:28px 32px;display:flex;align-items:center;gap:16px;border:1px solid #ede9fe}
        .hp-section-h2{font-size:22px;font-weight:700;color:#1a1a1a;margin:0 0 4px}
        .hp-section-sub{font-size:13.5px;color:#999;margin:0}
        .hp-link-btn{padding:8px 18px;background:#f5f5f7;color:#333;border:1px solid #e5e5e5;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer}
        .hp-link-btn:hover{background:#efefef}
        .hp-ext-link{display:inline-block;margin-top:12px;font-size:12px;color:#3b82f6;text-decoration:none;font-weight:500}

        @media(max-width:1100px){
          .hp-root{padding:0 16px}
          .hp-hero{padding:44px 36px 40px;border-radius:20px}
          .hp-title{font-size:30px;max-width:480px}
          .hp-desc{font-size:15px;max-width:450px}
        }
        @media(max-width:900px){
          .hp-grid-steps{grid-template-columns:repeat(2,1fr)!important}
          .hp-grid-tpls{grid-template-columns:repeat(2,1fr)!important}
          .hp-grid-apps{grid-template-columns:repeat(2,1fr)!important}
          .hp-hero{padding:36px 28px 34px}
          .hp-title{font-size:27px}
          .hp-desc{font-size:14.5px}
        }
        @media(max-width:680px){
          .hp-root{padding:0 12px}
          .hp-hero{padding:32px 20px 28px;border-radius:18px;margin:12px 0 24px}
          .hp-badge{font-size:12px;padding:5px 13px;margin-bottom:18px}
          .hp-title{font-size:24px;max-width:100%;letter-spacing:-.5px}
          .hp-desc{font-size:14px;max-width:100%;margin-bottom:24px;line-height:1.8}
          .hp-btns{flex-direction:column}
          .hp-btn-primary,.hp-btn-ghost{width:100%;text-align:center;justify-content:center}
          .hp-grid-steps,.hp-grid-tpls,.hp-grid-apps{grid-template-columns:1fr!important;gap:12px!important}
          .hp-card{padding:22px 18px}
          .hp-tpl{padding:18px 16px}
          .hp-tip{flex-direction:column;text-align:center;padding:22px 20px}
          .hp-empty{padding:36px 20px}
          .hp-section-h2{font-size:19px}
        }
      `}</style>

      <section className="hp-hero">
        <div className="hp-hero-glow"><div className="hp-hero-glow-1" /><div className="hp-hero-glow-2" /></div>
        <div style={{ position: "relative", zIndex: 1 }}>
          <div className="hp-badge"><span style={{ fontSize: 16 }}>\uD83D\uDC68\u200D\uD83C\uDFEB</span> 专为中小学教师打造的 AI 创课平台</div>
          <h1 className="hp-title">把时间还给课堂<br />把灵感还给<span>教育</span></h1>
          <p className="hp-desc">在这里，每一份教育初心都能被 AI 守护。<br />用自然语言描述你的创意，AI 帮你完成。</p>
          <div className="hp-btns">
            <button className="hp-btn-primary" onClick={() => navigate("/apps")}>\u2728 开始创作</button>
            <button className="hp-btn-ghost" onClick={() => document.getElementById("templates")?.scrollIntoView({ behavior: "smooth" })}>看看模板 \u2192</button>
          </div>
        </div>
      </section>

      <section style={{ marginBottom: 40 }}>
        <div className="hp-grid-steps" style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 20 }}>
          {STEPS.map((step, i) => (
            <div key={step.num} className="hp-card"
              onMouseEnter={(e) => { const el = e.currentTarget; el.style.boxShadow = "0 8px 30px rgba(0,0,0,0.06)"; el.style.transform = "translateY(-2px)"; }}
              onMouseLeave={(e) => { const el = e.currentTarget; el.style.boxShadow = ""; el.style.transform = ""; }}
            >
              <div className="hp-card-icon">{step.icon}</div>
              <div className="hp-card-num" style={{ background: i === 0 ? "#3b82f6" : i === 1 ? "#8b5cf6" : "#10b981" }}>{step.num}</div>
              <h3 className="hp-card-title">{step.title}</h3>
              <p className="hp-card-desc">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="templates" style={{ marginBottom: 40 }}>
        <div style={{ marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div><h2 className="hp-section-h2">\uD83C\uDFA8 从模板开始</h2><p className="hp-section-sub">选择一个场景，AI 会帮你生成对应的互动教学工具</p></div>
        </div>
        <div className="hp-grid-tpls" style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
          {TEMPLATES.map((t, idx) => (
            <div key={idx} className={`hp-tpl${selectedTemplate === idx ? " active" : ""}`} onClick={() => setSelectedTemplate(selectedTemplate === idx ? null : idx)} style={selectedTemplate === idx ? { "--tpl-color": t.color, "--tpl-bg": t.bg } as React.CSSProperties : undefined}
              onMouseEnter={(e) => { if (selectedTemplate !== idx) { e.currentTarget.style.borderColor = "#e0e0e0"; e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.04)"; } }}
              onMouseLeave={(e) => { if (selectedTemplate !== idx) { e.currentTarget.style.borderColor = ""; e.currentTarget.style.boxShadow = ""; } }}
            >
              <div className="hp-tpl-icon">{t.icon}</div>
              <h3 className="hp-tpl-title">{t.title}</h3>
              <p className="hp-tpl-desc">{t.desc}</p>
              {selectedTemplate === idx && (
                <div className="hp-tpl-detail">
                  <div className="hp-tpl-prompt-label">\uD83D\uDCA1 示例提示词：</div>
                  <div className="hp-tpl-prompt">{t.prompt}</div>
                  <button className="hp-tpl-go" onClick={(e) => { e.stopPropagation(); navigate("/apps"); }}>去创作 \u2192</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: 40 }}>
        <div style={{ marginBottom: 20, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div><h2 className="hp-section-h2">\uD83D\uDCC2 我的作品</h2><p className="hp-section-sub">你已创建的教学工具和应用</p></div>
          <button className="hp-link-btn" onClick={() => navigate("/apps")}>查看全部 \u2192</button>
        </div>
        {loading ? (<div style={{ textAlign: "center", padding: "60px 0", color: "#ccc", fontSize: 14 }}>加载中...</div>) : apps.length > 0 ? (
          <div className="hp-grid-apps" style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
            {apps.map((app) => (
              <div key={app.id} className="hp-app-card" onClick={() => navigate(`/apps/${app.id}`)}
                onMouseEnter={(e) => { const el = e.currentTarget; el.style.boxShadow = "0 6px 24px rgba(0,0,0,0.06)"; el.style.transform = "translateY(-2px)"; }}
                onMouseLeave={(e) => { const el = e.currentTarget; el.style.boxShadow = ""; el.style.transform = ""; }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10, flexWrap: "wrap", gap: 6 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "#1a1a1a", margin: 0 }}>{app.name}</h3>
                  <span className={`hp-status ${app.status === "running" ? "hp-status-running" : app.status === "stopped" ? "hp-status-stopped" : "hp-status-other"}`}>{({ running: "运行中", stopped: "已停止", building: "构建中", failed: "失败", pending: "等待中" }[app.status] || app.status)}</span>
                </div>
                {app.description && <p style={{ fontSize: 13, color: "#888", margin: 0, lineHeight: 1.5 }}>{app.description}</p>}
                {app.access_url && <a href={app.access_url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="hp-ext-link">\uD83D\uDD17 打开链接</a>}
              </div>
            ))}
          </div>
        ) : (
          <div className="hp-empty">
            <div style={{ fontSize: 48, marginBottom: 16 }}>\uD83C\uDF92</div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: "#1a1a1a", margin: "0 0 8px" }}>还没有作品</h3>
            <p style={{ fontSize: 14, color: "#999", margin: "0 0 24px", maxWidth: 360, marginLeft: "auto", marginRight: "auto", lineHeight: 1.7 }}>选择上方的模板开始你的第一个互动教学工具吧！<br />不需要任何编程基础，用说话的方式告诉 AI 就行。</p>
            <button style={{ padding: "12px 28px", background: "#0a0a0a", color: "#fff", border: "none", borderRadius: 11, fontSize: 14, fontWeight: 600, cursor: "pointer" }} onClick={() => navigate("/apps")}>+ 创建第一个应用</button>
          </div>
        )}
      </section>

      <div className="hp-tip">
        <div style={{ fontSize: 28, flexShrink: 0 }}>\uD83D\uDCA1</div>
        <div><div style={{ fontSize: 15, fontWeight: 600, color: "#1a1a1a", marginBottom: 3 }}>小贴士</div><div style={{ fontSize: 13, color: "#777", lineHeight: 1.7 }}>描述得越具体，AI 生成的效果越好。比如：「我想做一个初二物理的自由落体演示，小球从高处落下，显示速度和时间的变化曲线，界面要大字体适合投影」。遇到问题可以在 Skills 市场寻找更多帮助。</div></div>
      </div>
    </div>
  );
}
