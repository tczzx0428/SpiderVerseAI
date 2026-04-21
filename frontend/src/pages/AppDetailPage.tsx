import { Badge, Button, Card, Descriptions, Space, Spin, Tabs, Typography, message, Popconfirm } from "antd";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { deleteApp, downloadOutput, getApp, getAppHistory, getAppLogs, restartApp, stopApp, type AppItem, type RunRecord } from "@/api/apps";
import { useAuthStore } from "@/store/authStore";
import dayjs from "dayjs";

const STATUS_MAP: Record<string, { status: string; text: string }> = {
  pending: { status: "default", text: "待上传" },
  building: { status: "processing", text: "构建中" },
  running: { status: "success", text: "运行中" },
  stopped: { status: "warning", text: "已停止" },
  failed: { status: "error", text: "构建失败" },
};

export default function AppDetailPage() {
  const { appId } = useParams<{ appId: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [app, setApp] = useState<AppItem | null>(null);
  const [log, setLog] = useState("");
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<RunRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const logRef = useRef<HTMLPreElement>(null);

  const fetchApp = async () => {
    const res = await getApp(Number(appId));
    setApp(res.data);
  };

  const fetchLog = async () => {
    const res = await getAppLogs(Number(appId));
    setLog(res.data.log || "");
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await getAppHistory(Number(appId));
      setHistory(res.data);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([fetchApp(), fetchLog(), fetchHistory()]).finally(() => setLoading(false));

    const timer = setInterval(async () => {
      const res = await getApp(Number(appId));
      setApp(res.data);
      if (res.data.status === "building") {
        await fetchLog();
      } else {
        clearInterval(timer);
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [appId]);

  const handleStop = async () => {
    await stopApp(Number(appId));
    message.success("已停止");
    fetchApp();
  };

  const handleRestart = async () => {
    await restartApp(Number(appId));
    message.success("已重启");
    fetchApp();
  };

  const handleDelete = async () => {
    await deleteApp(Number(appId));
    message.success("已删除");
    navigate("/apps");
  };

  const handleDownload = async (record: RunRecord) => {
    setDownloading(record.run_id);
    try {
      await downloadOutput(Number(appId), record.run_id, record.output_filename);
    } catch {
      message.error("文件不存在或已删除");
    } finally {
      setDownloading(null);
    }
  };

  if (loading) return <Spin />;
  if (!app) return <Typography.Text>App 不存在</Typography.Text>;

  const s = STATUS_MAP[app.status] || { status: "default", text: app.status };
  const isAdmin = user?.role === "admin";
  const accessUrl = app.access_url
    ? `${app.access_url}?sv_user=${encodeURIComponent(user?.username || "")}`
    : undefined;

  const tabItems = [
    {
      key: "info",
      label: "基本信息",
      children: (
        <Card>
          <Descriptions column={2}>
            <Descriptions.Item label="状态">
              <Badge status={s.status as any} text={s.text} />
            </Descriptions.Item>
            <Descriptions.Item label="作者">{app.owner.username}</Descriptions.Item>
            <Descriptions.Item label="路径">/apps/{app.slug}</Descriptions.Item>
            <Descriptions.Item label="端口">{app.host_port || "-"}</Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(app.created_at).format("YYYY-MM-DD HH:mm")}
            </Descriptions.Item>
            <Descriptions.Item label="描述">{app.description || "-"}</Descriptions.Item>
          </Descriptions>
        </Card>
      ),
    },
    {
      key: "log",
      label: "构建日志",
      children: (
        <Card>
          <pre
            ref={logRef}
            style={{
              background: "#1e1e1e",
              color: "#d4d4d4",
              padding: 16,
              borderRadius: 6,
              minHeight: 200,
              maxHeight: 500,
              overflow: "auto",
              fontSize: 12,
              lineHeight: 1.5,
              margin: 0,
              whiteSpace: "pre-wrap",
              wordBreak: "break-all",
            }}
          >
            {log || "暂无日志"}
          </pre>
        </Card>
      ),
    },
    {
      key: "history",
      label: "运行历史",
      children: historyLoading ? (
        <div style={{ textAlign: "center", padding: 48 }}><Spin /></div>
      ) : history.length === 0 ? (
        <div style={{ textAlign: "center", padding: "48px 20px", color: "#999" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
          <div style={{ fontSize: 14 }}>暂无运行记录</div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {history.map((record) => (
            <div
              key={record.run_id}
              style={{ border: "1px solid #e5e5e5", borderRadius: 8, padding: 16, background: "#fff" }}
            >
              {/* 时间 + 用户（管理员可见）+ 版本号 */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ fontSize: 13, color: "#1a1a1a", fontWeight: 500 }}>
                    {dayjs(record.timestamp).format("YYYY-MM-DD HH:mm:ss")}
                  </span>
                  {isAdmin && (
                    <span style={{ fontSize: 12, color: "#666", background: "#f5f5f5", padding: "2px 8px", borderRadius: 4 }}>
                      {record.username}
                    </span>
                  )}
                  {record.app_version && (
                    <span style={{ fontSize: 12, color: "#999" }}>v{record.app_version}</span>
                  )}
                </div>
                <Button size="small" loading={downloading === record.run_id} onClick={() => handleDownload(record)}>
                  下载结果
                </Button>
              </div>

              {/* 摘要 */}
              <div style={{ fontSize: 13, color: "#666", marginBottom: 8 }}>{record.summary}</div>

              {/* 输入参数 */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {Object.entries(record.inputs).map(([k, v]) => (
                  <span key={k} style={{ fontSize: 12, color: "#666", background: "#f5f5f5", padding: "2px 8px", borderRadius: 4 }}>
                    {k}：{String(v)}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {app.name}
        </Typography.Title>
        <Space>
          {app.status === "running" && (
            <>
              <Button type="primary" href={accessUrl} target="_blank">
                访问应用
              </Button>
              <Button onClick={handleStop}>停止</Button>
            </>
          )}
          {app.status === "stopped" && (
            <Button type="primary" onClick={handleRestart}>重启</Button>
          )}
          <Popconfirm title="确认删除？" onConfirm={handleDelete}>
            <Button danger>删除</Button>
          </Popconfirm>
        </Space>
      </div>

      <Tabs items={tabItems} />
    </div>
  );
}
