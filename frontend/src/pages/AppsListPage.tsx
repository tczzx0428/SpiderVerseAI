import { Drawer, Dropdown, Input, Modal, Select, Spin, Tag, message, type MenuProps } from "antd";
import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { deleteApp, getAppHistory, getAppLogs, listApps, restartApp, stopApp, updateAppInfo, type AppItem, type RunRecord } from "@/api/apps";
import UploadModal from "@/components/UploadModal";
import { useAuthStore } from "@/store/authStore";
import client from "@/api/client";
import dayjs from "dayjs";
import type { User } from "@/api/auth";

const STATUS_DOT: Record<string, { color: string; text: string; tagColor: string }> = {
  pending:  { color: "#d0d0d0", text: "待上传",   tagColor: "default" },
  building: { color: "#f59e0b", text: "构建中",   tagColor: "processing" },
  running:  { color: "#22c55e", text: "运行中",   tagColor: "success" },
  stopped:  { color: "#9ca3af", text: "已停止",   tagColor: "warning" },
  failed:   { color: "#ef4444", text: "构建失败", tagColor: "error" },
};

const APP_ICONS = ["📊", "🎨", "🔧", "📝", "🎯", "🔍", "💡", "🚀", "⚡", "🛠"];

function stripMarkdown(text: string): string {
  return text
    .replace(/^#+\s+/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/`{1,3}[^`]*`{1,3}/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^[-*>\s]+/gm, "")
    .replace(/\n+/g, " ")
    .trim();
}

function AppCard({
  app, canManage, isAdmin, isActing, onStop, onRestart, onDelete, onDetail, onUpdate, onEdit,
}: {
  app: AppItem;
  canManage: boolean;
  isAdmin: boolean;
  isActing: boolean;
  onStop: () => void;
  onRestart: () => void;
  onDelete: () => void;
  onDetail: () => void;
  onUpdate: () => void;
  onEdit: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const s = STATUS_DOT[app.status] || { color: "#d0d0d0", text: app.status, tagColor: "default" };
  const icon = APP_ICONS[app.id % APP_ICONS.length];
  const isRunning = app.status === "running";

  const handleCardClick = () => {
    if (isRunning && app.access_url) {
      const uname = useAuthStore.getState().user?.username || "";
      const sep = app.access_url.includes("?") ? "&" : "?";
      const url = app.access_url + sep + "sv_user=" + encodeURIComponent(uname);
      // 记录一次访问
      client.post(`/apps/internal/view/${app.id}`, { username: uname }).catch(() => {});
      window.open(url, "_blank");
    }
  };

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    const url = window.location.origin + app.access_url;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(() => message.success("链接已复制")).catch(() => {
        fallbackCopy(url);
      });
    } else {
      fallbackCopy(url);
    }
  };

  const fallbackCopy = (text: string) => {
    const el = document.createElement("textarea");
    el.value = text;
    el.style.position = "fixed";
    el.style.opacity = "0";
    document.body.appendChild(el);
    el.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(el);
    if (ok) message.success("链接已复制");
    else message.error("复制失败，请手动复制：" + text);
  };

  const menuItems: MenuProps["items"] = [
    {
      key: "detail",
      label: "查看详情",
      disabled: isActing,
      onClick: ({ domEvent }) => { domEvent.stopPropagation(); onDetail(); },
    },
  ];
  if (isAdmin) {
    menuItems.push({
      key: "edit",
      label: "编辑信息",
      disabled: isActing,
      onClick: ({ domEvent }) => { domEvent.stopPropagation(); onEdit(); },
    });
  }
  if (canManage) {
    menuItems.push({
      key: "update",
      label: "更新应用",
      disabled: isActing,
      onClick: ({ domEvent }) => { domEvent.stopPropagation(); onUpdate(); },
    });
  }
  if (canManage && isRunning) {
    menuItems.push({
      key: "stop",
      label: "停止应用",
      disabled: isActing,
      onClick: ({ domEvent }) => { domEvent.stopPropagation(); onStop(); },
    });
  }
  if (canManage && app.status === "stopped") {
    menuItems.push({
      key: "restart",
      label: "启动应用",
      disabled: isActing,
      onClick: ({ domEvent }) => { domEvent.stopPropagation(); onRestart(); },
    });
  }
  if (canManage) {
    menuItems.push({ type: "divider" });
    menuItems.push({
      key: "delete",
      label: <span style={{ color: isActing ? "#ccc" : "#ef4444" }}>删除应用</span>,
      disabled: isActing,
      onClick: ({ domEvent }) => {
        domEvent.stopPropagation();
        Modal.confirm({
          title: "确认删除该应用？",
          content: "删除后无法恢复",
          okText: "删除",
          okButtonProps: { danger: true },
          onOk: onDelete,
        });
      },
    });
  }

  return (
    <div
      style={{
        background: "#fff",
        border: `1px solid ${hovered ? "#d0d0d0" : "#e5e5e5"}`,
        borderRadius: 12,
        padding: 24,
        transition: "all 0.2s ease",
        transform: hovered ? "translateY(-2px)" : "none",
        boxShadow: hovered ? "0 4px 16px rgba(0,0,0,0.08)" : "none",
        cursor: isRunning ? "pointer" : "default",
        position: "relative",
        display: "flex",
        flexDirection: "column",
      }}
      onClick={handleCardClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* 复制链接（右上角，仅 running） */}
      {isRunning && (
        <button
          onClick={handleCopy}
          style={{
            position: "absolute", top: 14, right: 14,
            padding: "3px 10px",
            background: "#f5f5f5", color: "#555",
            border: "1px solid #e5e5e5", borderRadius: 20,
            fontSize: 11, fontWeight: 500, cursor: "pointer",
            display: "flex", alignItems: "center", gap: 4,
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            const el = e.currentTarget as HTMLElement;
            el.style.background = "#ebebeb";
            el.style.borderColor = "#d0d0d0";
          }}
          onMouseLeave={(e) => {
            const el = e.currentTarget as HTMLElement;
            el.style.background = "#f5f5f5";
            el.style.borderColor = "#e5e5e5";
          }}
        >
          🔗 复制链接
        </button>
      )}

      {/* 图标 */}
      <div style={{
        width: 56, height: 56, borderRadius: 12,
        background: "linear-gradient(135deg, #2c2c2c, #1a1a1a)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 28, marginBottom: 16,
      }}>
        {icon}
      </div>

      {/* 名称 + 状态 */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: "#1a1a1a", letterSpacing: "-0.3px", margin: 0, paddingRight: 8 }}>
          {app.name}
        </h3>
        <span style={{ display: "flex", alignItems: "center", gap: 5, flexShrink: 0 }}>
          <span style={{
            width: 7, height: 7, borderRadius: "50%", background: s.color,
            boxShadow: isRunning ? `0 0 6px ${s.color}` : "none",
            display: "inline-block",
          }} />
          <span style={{ fontSize: 12, color: "#999" }}>{s.text}</span>
        </span>
      </div>

      {/* 描述 */}
      {app.description && (
        <p style={{
          fontSize: 13, color: "#666", margin: "0 0 10px",
          overflow: "hidden", display: "-webkit-box",
          WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
          lineHeight: 1.5,
        }}>
          {stripMarkdown(app.description)}
        </p>
      )}

      {/* 元信息 */}
      <div style={{ display: "flex", flexDirection: "column", gap: 5, flex: 1 }}>
        <div style={{ display: "flex", gap: 8, fontSize: 13 }}>
          <span style={{ color: "#999", minWidth: 44 }}>作者</span>
          <span style={{ color: "#1a1a1a", fontWeight: 500 }}>{app.owner.username}</span>
        </div>
        <div style={{ display: "flex", gap: 8, fontSize: 13 }}>
          <span style={{ color: "#999", minWidth: 44 }}>工具最近更新时间</span>
          <span style={{ color: "#1a1a1a", fontWeight: 500 }}>{dayjs(app.updated_at).format("YYYY-MM-DD HH:mm")}</span>
        </div>
      </div>

      {/* 底部：三点菜单 */}
      <div
        style={{ display: "flex", justifyContent: "flex-end", marginTop: 16 }}
        onClick={(e) => e.stopPropagation()}
      >
        <Dropdown menu={{ items: menuItems }} trigger={isActing ? [] : ["click"]} placement="bottomRight">
          <button
            style={{
              padding: "4px 12px",
              background: "transparent", color: isActing ? "#ddd" : "#aaa",
              border: `1px solid ${isActing ? "#f0f0f0" : "#e5e5e5"}`, borderRadius: 6,
              fontSize: 18, cursor: isActing ? "not-allowed" : "pointer", lineHeight: 1,
              letterSpacing: 1, transition: "all 0.15s",
            }}
            onMouseEnter={(e) => {
              if (isActing) return;
              const el = e.currentTarget as HTMLElement;
              el.style.borderColor = "#c0c0c0";
              el.style.color = "#555";
            }}
            onMouseLeave={(e) => {
              if (isActing) return;
              const el = e.currentTarget as HTMLElement;
              el.style.borderColor = "#e5e5e5";
              el.style.color = "#aaa";
            }}
          >{isActing ? "…" : "···"}</button>
        </Dropdown>
      </div>
    </div>
  );
}

export default function AppsListPage() {
  const [apps, setApps] = useState<AppItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [updateTarget, setUpdateTarget] = useState<AppItem | null>(null);
  const [editTarget, setEditTarget] = useState<AppItem | null>(null);
  const [editForm, setEditForm] = useState<{ name: string; description: string; owner_id: number }>({ name: "", description: "", owner_id: 0 });
  const [editSaving, setEditSaving] = useState(false);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [detailApp, setDetailApp] = useState<AppItem | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [detailLog, setDetailLog] = useState<string>("");
  const [logLoading, setLogLoading] = useState(false);
  const [runHistory, setRunHistory] = useState<RunRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const logRef = useRef<HTMLPreElement>(null);
  const logTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { user } = useAuthStore();

  // 打开 Drawer 时拉取构建日志 + 使用记录
  useEffect(() => {
    if (logTimerRef.current) clearInterval(logTimerRef.current);
    setDetailLog("");
    setRunHistory([]);
    if (!detailApp) return;

    // 拉取构建日志
    const fetchLog = async () => {
      try {
        const res = await getAppLogs(detailApp.id);
        setDetailLog(res.data.log || "");
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
      } catch { /* ignore */ }
    };

    setLogLoading(true);
    fetchLog().finally(() => setLogLoading(false));

    if (detailApp.status === "building") {
      logTimerRef.current = setInterval(async () => {
        const res = await getAppLogs(detailApp.id);
        const newLog = res.data.log || "";
        setDetailLog(newLog);
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
        if (res.data.status !== "building") {
          clearInterval(logTimerRef.current!);
          fetchApps();
        }
      }, 3000);
    }

    // 拉取使用记录
    setHistoryLoading(true);
    getAppHistory(detailApp.id)
      .then((res) => setRunHistory(res.data))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));

    return () => { if (logTimerRef.current) clearInterval(logTimerRef.current); };
  }, [detailApp?.id]);

  const filteredApps = useMemo(() => {
    const kw = search.trim().toLowerCase();
    return apps.filter((a) => {
      if (kw && !a.name.toLowerCase().includes(kw) && !a.owner.username.toLowerCase().includes(kw)) return false;
      if (statusFilter !== "all" && a.status !== statusFilter) return false;
      return true;
    });
  }, [apps, search, statusFilter]);

  const fetchApps = async () => {
    setLoading(true);
    try {
      const res = await listApps({ page: 1, size: 100 });
      setApps(res.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
    const timer = setInterval(fetchApps, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleStop = async (id: number) => {
    setActionLoading(id);
    try { await stopApp(id); message.success("已停止"); fetchApps(); }
    finally { setActionLoading(null); }
  };
  const handleRestart = async (id: number) => {
    setActionLoading(id);
    try { await restartApp(id); message.success("已启动"); fetchApps(); }
    finally { setActionLoading(null); }
  };
  const handleDelete = async (id: number) => {
    setActionLoading(id);
    try {
      await deleteApp(id); message.success("已删除");
      setDetailApp(null); fetchApps();
    } finally { setActionLoading(null); }
  };

  const canManage = (app: AppItem) =>
    user?.role === "admin" || user?.id === app.owner.id;

  const isAdmin = user?.role === "admin";

  const handleOpenEdit = async (app: AppItem) => {
    setEditTarget(app);
    setEditForm({ name: app.name, description: app.description || "", owner_id: app.owner.id });
    if (allUsers.length === 0) {
      try {
        const res = await client.get<User[]>("/admin/users");
        setAllUsers(res.data);
      } catch { /* ignore */ }
    }
  };

  const handleSaveEdit = async () => {
    if (!editTarget) return;
    setEditSaving(true);
    try {
      await updateAppInfo(editTarget.id, {
        name: editForm.name,
        description: editForm.description,
        owner_id: editForm.owner_id,
      });
      message.success("修改成功");
      setEditTarget(null);
      fetchApps();
    } catch {
      message.error("修改失败");
    } finally {
      setEditSaving(false);
    }
  };

  const s = detailApp ? (STATUS_DOT[detailApp.status] || { text: detailApp.status, tagColor: "default" }) : null;

  return (
    <div>
      {/* 头部 */}
      <div style={{
        position: "sticky", top: 0, zIndex: 10,
        background: "#fafafa",
        padding: "32px 0 20px",
        marginBottom: 4,
        borderBottom: "1px solid #f0f0f0",
        display: "flex", justifyContent: "space-between", alignItems: "flex-start",
      }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: "#1a1a1a", letterSpacing: "-0.5px", margin: "0 0 4px" }}>
            应用管理
          </h1>
          <p style={{ fontSize: 14, color: "#666", margin: 0 }}>
            查看和管理所有应用
          </p>
        </div>
        {apps.length > 0 && (
          <button
            onClick={() => setUploadOpen(true)}
            style={{
              padding: "12px 24px", background: "#2c2c2c", color: "#fff",
              border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600,
              cursor: "pointer", display: "flex", alignItems: "center", gap: 8,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#1a1a1a"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "#2c2c2c"; }}
          >
            <span>＋</span> 上传 App
          </button>
        )}
      </div>

      {/* 筛选栏 */}
      {apps.length > 0 && <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center", flexWrap: "wrap" }}>
        <Input.Search
          placeholder="搜索应用名或创建者..."
          allowClear
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 240 }}
        />
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 140 }}
          options={[
            { value: "all", label: "全部状态" },
            { value: "running", label: "运行中" },
            { value: "stopped", label: "已停止" },
            { value: "building", label: "构建中" },
            { value: "failed", label: "构建失败" },
          ]}
        />
        {(search || statusFilter !== "all") && (
          <span style={{ fontSize: 13, color: "#999" }}>
            {filteredApps.length} / {apps.length} 个应用
          </span>
        )}
      </div>}

      {/* 内容 */}
      {loading && apps.length === 0 ? (
        <div style={{ textAlign: "center", padding: 80 }}><Spin /></div>
      ) : filteredApps.length === 0 ? (
        <div style={{ textAlign: "center", padding: "80px 20px" }}>
          <div style={{
            width: 80, height: 80, margin: "0 auto 24px",
            background: "#f0f0f0", borderRadius: "50%",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40,
          }}>📱</div>
          <h3 style={{ fontSize: 20, fontWeight: 600, color: "#1a1a1a", margin: "0 0 8px" }}>
            {apps.length === 0 ? "暂无应用" : "没有匹配的应用"}
          </h3>
          {apps.length === 0 && (
            <>
              <p style={{ color: "#666", marginBottom: 24 }}>上传你的第一个 App 吧</p>
              <button
                onClick={() => setUploadOpen(true)}
                style={{
                  padding: "12px 24px", background: "#2c2c2c", color: "#fff",
                  border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer",
                }}
              >＋ 上传 App</button>
            </>
          )}
        </div>
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
          gap: 24,
        }}>
          {filteredApps.map((app) => (
            <AppCard
              key={app.id}
              app={app}
              canManage={canManage(app)}
              isAdmin={!!isAdmin}
              isActing={actionLoading === app.id}
              onStop={() => handleStop(app.id)}
              onRestart={() => handleRestart(app.id)}
              onDelete={() => handleDelete(app.id)}
              onDetail={() => setDetailApp(app)}
              onUpdate={() => setUpdateTarget(app)}
              onEdit={() => handleOpenEdit(app)}
            />
          ))}
        </div>
      )}

      {/* 详情 Drawer */}
      <Drawer
        title={detailApp?.name}
        open={!!detailApp}
        onClose={() => setDetailApp(null)}
        width={520}
        extra={detailApp && s && <Tag color={s.tagColor}>{s.text}</Tag>}
      >
        {detailApp && (
          <div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 24 }}>
              <div style={{ display: "flex", gap: 12 }}>
                <span style={{ color: "#999", width: 64 }}>创建者</span>
                <span style={{ fontWeight: 500 }}>{detailApp.owner.username}</span>
              </div>
              <div style={{ display: "flex", gap: 12 }}>
                <span style={{ color: "#999", width: 64 }}>创建时间</span>
                <span>{dayjs(detailApp.created_at).format("YYYY-MM-DD HH:mm")}</span>
              </div>
              <div style={{ display: "flex", gap: 12 }}>
                <span style={{ color: "#999", width: 64 }}>更新时间</span>
                <span>{dayjs(detailApp.updated_at).format("YYYY-MM-DD HH:mm")}</span>
              </div>
              {detailApp.status === "running" && detailApp.access_url && (
                <div style={{ display: "flex", gap: 12 }}>
                  <span style={{ color: "#999", width: 64 }}>访问地址</span>
                  <a href={detailApp.access_url + "?sv_user=" + encodeURIComponent(user?.username || "")} target="_blank" rel="noreferrer">
                    {window.location.origin + detailApp.access_url}
                  </a>
                </div>
              )}
            </div>

            {/* 应用说明 */}
            <div style={{ borderTop: "1px solid #f0f0f0", paddingTop: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a", marginBottom: 12 }}>应用说明</div>
              {detailApp.description ? (
                <div style={{ fontSize: 14, color: "#333", lineHeight: 1.8 }}>
                  <ReactMarkdown>{detailApp.description}</ReactMarkdown>
                </div>
              ) : (
                <div style={{ color: "#999", fontSize: 13 }}>暂无说明（上传包含 README.md 的 zip 后自动读取）</div>
              )}
            </div>

            {/* 使用记录 */}
            <div style={{ borderTop: "1px solid #f0f0f0", paddingTop: 20, marginTop: 20 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a" }}>使用记录</span>
                {runHistory.length > 0 && (
                  <span style={{ fontSize: 11, color: "#999" }}>共 {runHistory.length} 条</span>
                )}
              </div>
              {historyLoading ? (
                <div style={{ textAlign: "center", padding: 16 }}><Spin size="small" /></div>
              ) : runHistory.length === 0 ? (
                <div style={{ color: "#bbb", fontSize: 13, textAlign: "center", padding: "12px 0" }}>暂无使用记录</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {runHistory.map((r, idx) => (
                    <div key={r.run_id || idx} style={{
                      background: "#f9f9f9", borderRadius: 8,
                      padding: "10px 12px",
                      border: "1px solid #f0f0f0",
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: r.summary ? 4 : 0 }}>
                        <span style={{ fontSize: 12, color: "#1a1a1a", fontWeight: 500 }}>
                          {r.username}
                        </span>
                        <span style={{ fontSize: 11, color: "#bbb" }}>
                          {dayjs(r.timestamp).format("MM-DD HH:mm")}
                        </span>
                      </div>
                      {r.summary && (
                        <div style={{ fontSize: 12, color: "#666", lineHeight: 1.5 }}>
                          {r.summary}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 构建日志 */}
            <div style={{ borderTop: "1px solid #f0f0f0", paddingTop: 20, marginTop: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a" }}>构建日志</span>
                {detailApp.status === "building" && (
                  <span style={{ fontSize: 11, color: "#f59e0b", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 4, padding: "1px 6px" }}>
                    构建中…
                  </span>
                )}
              </div>
              {logLoading ? (
                <div style={{ textAlign: "center", padding: 20 }}><Spin size="small" /></div>
              ) : (
                <pre
                  ref={logRef}
                  style={{
                    background: "#1e1e1e", color: "#d4d4d4",
                    padding: 12, borderRadius: 6, margin: 0,
                    fontSize: 11, lineHeight: 1.5,
                    maxHeight: 300, overflow: "auto",
                    whiteSpace: "pre-wrap", wordBreak: "break-all",
                  }}
                >
                  {detailLog || "暂无日志"}
                </pre>
              )}
            </div>

            {/* 操作按钮 */}
            {canManage(detailApp) && (
              <div style={{ borderTop: "1px solid #f0f0f0", paddingTop: 20, marginTop: 20, display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  onClick={() => { setUpdateTarget(detailApp); setDetailApp(null); }}
                  style={btnStyle("#f0f7ff", "#165DFF", "1px solid #bfdbfe")}
                >更新应用</button>
                {detailApp.status === "running" && (
                  <button
                    onClick={() => { handleStop(detailApp.id); setDetailApp(null); }}
                    style={btnStyle("#f0f0f0", "#666")}
                  >停止</button>
                )}
                {detailApp.status === "stopped" && (
                  <button
                    onClick={() => { handleRestart(detailApp.id); setDetailApp(null); }}
                    style={btnStyle("#2c2c2c", "#fff")}
                  >启动</button>
                )}
                <button
                  onClick={() => Modal.confirm({
                    title: "确认删除该应用？",
                    content: "删除后无法恢复",
                    okText: "删除",
                    okButtonProps: { danger: true },
                    onOk: () => handleDelete(detailApp.id),
                  })}
                  style={btnStyle("#fff1f0", "#ef4444", "1px solid #fecaca")}
                >删除应用</button>
              </div>
            )}
          </div>
        )}
      </Drawer>

      {/* 新建 App 弹窗 */}
      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={() => { setUploadOpen(false); setTimeout(fetchApps, 1000); }}
      />

      {/* 更新 App 弹窗 */}
      <UploadModal
        open={!!updateTarget}
        onClose={() => setUpdateTarget(null)}
        onSuccess={() => { setUpdateTarget(null); setTimeout(fetchApps, 1000); }}
        targetApp={updateTarget ? { id: updateTarget.id, name: updateTarget.name } : undefined}
      />

      {/* 编辑信息弹窗（仅管理员） */}
      <Modal
        title="编辑应用信息"
        open={!!editTarget}
        onCancel={() => setEditTarget(null)}
        onOk={handleSaveEdit}
        confirmLoading={editSaving}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        {editTarget && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, padding: "12px 0" }}>
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#333", marginBottom: 6 }}>
                应用名称
              </label>
              <Input
                value={editForm.name}
                onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="应用名称"
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#333", marginBottom: 6 }}>
                应用说明
              </label>
              <Input.TextArea
                value={editForm.description}
                onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="应用说明（支持 Markdown）"
                autoSize={{ minRows: 3, maxRows: 8 }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#333", marginBottom: 6 }}>
                所有者
              </label>
              <Select
                value={editForm.owner_id}
                onChange={(v) => setEditForm((f) => ({ ...f, owner_id: v }))}
                style={{ width: "100%" }}
                showSearch
                optionFilterProp="label"
                options={allUsers.map((u) => ({ value: u.id, label: u.username }))}
              />
            </div>
            <div style={{ fontSize: 12, color: "#999" }}>
              Slug: <code style={{ background: "#f5f5f5", padding: "1px 4px", borderRadius: 3 }}>{editTarget.slug}</code>
              <span style={{ marginLeft: 8 }}>（Slug 不可修改）</span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function btnStyle(bg: string, color: string, border = "none"): React.CSSProperties {
  return {
    padding: "5px 12px", background: bg, color, border,
    borderRadius: 6, fontSize: 12, fontWeight: 500,
    cursor: "pointer", transition: "opacity 0.15s",
  };
}
