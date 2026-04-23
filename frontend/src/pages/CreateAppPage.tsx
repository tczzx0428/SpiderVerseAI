import { useState, useEffect, useRef } from "react";
import {
  Card,
  Input,
  Button,
  message,
  Progress,
  Tag,
  Space,
  List,
  Typography,
  Spin,
  Empty,
  Modal,
  Result,
} from "antd";
import {
  RobotOutlined,
  SendOutlined,
  PlusOutlined,
  HistoryOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
  LinkOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import {
  createNewSession,
  sendMessage,
  startCreation,
  getCreationStatus,
  listCreations,
  deleteCreation,
  type AICreation,
  type ChatMessage,
} from "@/api/aiCreate";

const { Title, Text, Paragraph } = Typography;

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  chatting: { color: "blue", label: "对话中" },
  generating: { color: "processing", label: "生成中" },
  building: { color: "processing", label: "构建中" },
  running: { color: "success", label: "已完成" },
  failed: { color: "error", label: "失败" },
  cancelled: { color: "default", label: "已取消" },
};

export default function CreateAppPage() {
  const navigate = useNavigate();

  const [view, setView] = useState<"chat" | "history">("chat");
  const [currentId, setCurrentId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<AICreation | null>(null);
  const [polling, setPolling] = useState(false);
  const [historyList, setHistoryList] = useState<AICreation[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current && messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (polling && currentId) {
      const timer = setInterval(async () => {
        try {
          const res = await getCreationStatus(currentId);
          setStatus(res.data);
          if (res.data.status === "running" || res.data.status === "failed") {
            setPolling(false);
            if (res.data.status === "running") {
              message.success("应用创建成功！");
            }
          }
        } catch {}
      }, 2000);
      return () => clearInterval(timer);
    }
  }, [polling, currentId]);

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await listCreations();
      setHistoryList(res.data);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      setLoading(true);
      const res = await createNewSession("新创作");
      setCurrentId(res.data.id);
      setMessages([]);
      setStatus(res.data);
      setView("chat");
      message.success("已创建新的对话");
    } catch (e: any) {
      message.error(e.response?.data?.detail || "创建失败");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim() || !currentId || loading) return;

    const userMsg = inputValue.trim();
    setInputValue("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await sendMessage(currentId, userMsg);
      setMessages(res.data.conversation);
    } catch (e: any) {
      message.error(e.response?.data?.detail || "发送失败");
    } finally {
      setLoading(false);
    }
  };

  const handleStartCreate = async () => {
    if (!currentId) return;

    Modal.confirm({
      title: "确认开始创建？",
      content: "确认后AI将根据你的需求自动生成代码并部署应用",
      okText: "开始创建",
      cancelText: "再聊聊",
      onOk: async () => {
        try {
          setLoading(true);
          await startCreation(currentId);
          setPolling(true);
          message.info("正在分析需求并生成代码...");
        } catch (e: any) {
          message.error(e.response?.data?.detail || "启动失败");
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const handleSelectHistory = (item: AICreation) => {
    setCurrentId(item.id);
    setStatus(item);
    setView("chat");
  };

  const handleDeleteHistory = async (id: number) => {
    try {
      await deleteCreation(id);
      setHistoryList((prev) => prev.filter((i) => i.id !== id));
      if (currentId === id) {
        setCurrentId(null);
        setMessages([]);
        setStatus(null);
      }
      message.success("已删除");
    } catch {
      message.error("删除失败");
    }
  };

  const renderChatView = () => (
    <div style={{ display: "flex", gap: 24, flex: 1, minHeight: 0 }}>
      <Card
        title={
          <Space>
            <RobotOutlined />
            <span>AI 助手</span>
            {status && <Tag color={STATUS_MAP[status.status]?.color}>{STATUS_MAP[status.status]?.label}</Tag>}
          </Space>
        }
        style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
        styles={{
          body: { flex: 1, display: "flex", flexDirection: "column", padding: 0, overflow: "hidden", minHeight: 0 },
        }}
        extra={
          status?.status === "chatting" && messages.length > 0 ? (
            <Button type="primary" icon={<CheckCircleOutlined />} onClick={handleStartCreate}>
              确认需求，开始创作
            </Button>
          ) : null
        }
      >
        <div
          ref={messagesContainerRef}
          style={{ flex: 1, overflowY: "auto", padding: "16px 24px", background: "#fafafa" }}
        >
          {!currentId ? (
            <Empty
              description="点击「新建对话」开始与AI助手交流"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" icon={<PlusOutlined />} onClick={handleNewChat}>
                新建对话
              </Button>
            </Empty>
          ) : (
            <>
              {messages.length === 0 && (
                <div style={{ textAlign: "center", padding: "40px 0", color: "#999" }}>
                  <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                  <p>你好！我是AI应用开发助手</p>
                  <p>告诉我你想创建什么应用，我会帮你一步步完成</p>
                </div>
              )}
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    marginBottom: 16,
                    display: "flex",
                    justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      maxWidth: "70%",
                      padding: "12px 16px",
                      borderRadius: 12,
                      background: msg.role === "user" ? "#165DFF" : "#fff",
                      color: msg.role === "user" ? "#fff" : "#1a1a1a",
                      boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                    }}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
                  <div
                    style={{
                      padding: "12px 16px",
                      borderRadius: 12,
                      background: "#fff",
                      boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                    }}
                  >
                    <Spin indicator={<LoadingOutlined style={{ fontSize: 16 }} spin />}>思考中...</Spin>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {currentId && status?.status === "chatting" && (
          <div
            style={{
              padding: "16px 24px",
              borderTop: "1px solid #f0f0f0",
              background: "#fff",
              flexShrink: 0,
            }}
          >
            <Input.TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="描述你想要创建的应用..."
              autoSize={{ minRows: 2, maxRows: 4 }}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading}
            />
            <div style={{ marginTop: 8, display: "flex", justifyContent: "flex-end" }}>
              <Space>
                <Button onClick={() => setView("history")}>
                  <HistoryOutlined /> 历史
                </Button>
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  loading={loading}
                  disabled={!inputValue.trim()}
                >
                  发送
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Card>

      {(status && status.status !== "chatting") && (
        <Card
          title="创建进度"
          style={{ width: 360, flexShrink: 0 }}
          styles={{ body: { padding: 16 } }}
        >
          {status.status === "failed" ? (
            <Result
              status="error"
              title="创建失败"
              subTitle={status.error_message}
              extra={[
                <Button key="retry" type="primary" onClick={handleNewChat}>
                  重试
                </Button>,
              ]}
            />
          ) : status.status === "running" ? (
            <Result
              status="success"
              title="创建成功！"
              subTitle={`应用已部署完成`}
              extra={[
                <Button key="view" type="primary" icon={<LinkOutlined />} onClick={() => navigate(`/apps/${status.app_id}`)}>
                  查看应用
                </Button>,
                <Button key="new" icon={<PlusOutlined />} onClick={handleNewChat}>
                  再创建一个
                </Button>,
              ]}
            />
          ) : (
            <div>
              <Progress percent={status.progress} status="active" strokeColor="#165DFF" />
              <Text type="secondary" style={{ marginTop: 8, display: "block" }}>
                {status.progress_message || "处理中..."}
              </Text>

              <div style={{ marginTop: 24 }}>
                <Title level={5}>步骤说明</Title>
                <Space direction="vertical" style={{ width: "100%" }} size={4}>
                  {[
                    { label: "分析需求", threshold: 10 },
                    { label: "生成代码", threshold: 20 },
                    { label: "创建应用", threshold: 40 },
                    { label: "打包上传", threshold: 50 },
                    { label: "构建镜像", threshold: 75 },
                    { label: "部署运行", threshold: 100 },
                  ].map((step) => (
                    <div
                      key={step.label}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        color: status.progress >= step.threshold ? "#165DFF" : "#999",
                      }}
                    >
                      {status.progress >= step.threshold ? (
                        <CheckCircleOutlined />
                      ) : (
                        <LoadingOutlined spin={status.progress > (step.threshold - 10)} />
                      )}
                      <span>{step.label}</span>
                    </div>
                  ))}
                </Space>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );

  const renderHistoryView = () => (
    <Card
      title={<Space><HistoryOutlined /> 创作历史</Space>}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { handleNewChat(); setView("chat"); }}>
          新建对话
        </Button>
      }
    >
      <Spin spinning={historyLoading}>
        <List
          dataSource={historyList}
          locale={{ emptyText: "暂无创作记录" }}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  key="open"
                  type="link"
                  onClick={() => handleSelectHistory(item)}
                >
                  查看
                </Button>,
                item.app_id && (
                  <Button
                    key="app"
                    type="link"
                    onClick={() => navigate(`/apps/${item.app_id}`)}
                  >
                    <LinkOutlined /> 应用
                  </Button>
                ),
                <Button
                  key="delete"
                  type="link"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDeleteHistory(item.id)},
                />,
              ]}
            >
              <List.Item.Meta
                title={item.title || `创作 #${item.id}`}
                description={
                  <Space>
                    <Tag color={STATUS_MAP[item.status]?.color}>
                      {STATUS_MAP[item.status]?.label}
                    </Tag>
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                  </Space>
                }
              />
              {item.status === "running" && item.app_id && (
                <Tag color="success">已部署</Tag>
              )}
            </List.Item>
          )}
        />
      </Spin>
    </Card>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)" }}>
      <div style={{ flexShrink: 0, marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Title level={3} style={{ margin: 0 }}>
            <RobotOutlined style={{ marginRight: 8 }} />
            创作应用
          </Title>
          <Space>
            <Button
              type={view === "chat" ? "primary" : "default"}
              onClick={() => setView("chat")}
            >
              对话
            </Button>
            <Button
              type={view === "history" ? "primary" : "default"}
              onClick={() => { setView("history"); loadHistory(); }}
            >
              <HistoryOutlined /> 历史
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleNewChat} loading={loading}>
              新建对话
            </Button>
          </Space>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        {view === "chat" ? renderChatView() : renderHistoryView()}
      </div>
    </div>
  );
}