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
  UserOutlined,
  ClockCircleOutlined,
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

  useEffect(() => {
    const styleId = "create-app-animations";
    if (!document.getElementById(styleId)) {
      const style = document.createElement("style");
      style.id = styleId;
      style.textContent = `
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

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

  const handleSend = async (text?: string) => {
    const msgText = text || inputValue.trim();
    if (!msgText || !currentId || loading) return;

    if (!text) setInputValue("");
    setMessages((prev) => [...prev, { role: "user", content: msgText }]);
    setLoading(true);

    try {
      const res = await sendMessage(currentId, msgText);
      const updatedConversation = res.data.conversation;
      if (res.data.options && res.data.options.length > 0) {
        const lastAssistantMsg = updatedConversation.filter(m => m.role === "assistant").pop();
        if (lastAssistantMsg) {
          lastAssistantMsg.options = res.data.options;
          lastAssistantMsg.suggest_start = res.data.suggest_start;
        }
      }
      setMessages(updatedConversation);
    } catch (e: any) {
      message.error(e.response?.data?.detail || "发送失败");
    } finally {
      setLoading(false);
    }
  };

  const handleOptionClick = (option: string, suggestStart?: boolean) => {
    if (suggestStart || option.includes("开始制作") || option.includes("开始创建") || option.includes("就这样")) {
      Modal.confirm({
        title: "确认开始创建？",
        content: "确认后AI将根据你的需求自动生成代码并部署应用",
        okText: "开始创建",
        cancelText: "再聊聊",
        onOk: async () => {
          if (!currentId) return;
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
    } else {
      handleSend(option);
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
          status?.status === "chatting" && messages.length > 1 ? (
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
              {messages.map((msg, idx) => {
                const isUser = msg.role === "user";
                const showOptions = !isUser && msg.options && msg.options.length > 0;

                return (
                  <div
                    key={idx}
                    style={{
                      marginBottom: showOptions ? 20 : 24,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: isUser ? "flex-end" : "flex-start",
                      animation: `fadeInUp 0.3s ease-out`,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "flex-end", gap: 10, maxWidth: "75%" }}>
                      {!isUser && (
                        <div
                          style={{
                            width: 36,
                            height: 36,
                            borderRadius: "50%",
                            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            flexShrink: 0,
                            boxShadow: "0 2px 8px rgba(102, 126, 234, 0.3)",
                          }}
                        >
                          <RobotOutlined style={{ color: "#fff", fontSize: 18 }} />
                        </div>
                      )}

                      <div
                        style={{
                          maxWidth: "100%",
                          position: "relative",
                        }}
                      >
                        <div
                          style={{
                            padding: "14px 18px",
                            borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                            background: isUser
                              ? "linear-gradient(135deg, #165DFF 0%, #4080FF 100%)"
                              : "linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)",
                            color: isUser ? "#fff" : "#1a1a1a",
                            boxShadow: isUser
                              ? "0 4px 12px rgba(22, 93, 255, 0.25)"
                              : "0 2px 12px rgba(0, 0, 0, 0.08)",
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                            lineHeight: 1.6,
                            fontSize: 14,
                            border: isUser ? "none" : "1px solid #e8e8e8",
                            transition: "all 0.2s ease",
                          }}
                        >
                          {msg.content}
                        </div>

                        <div
                          style={{
                            marginTop: 6,
                            display: "flex",
                            alignItems: "center",
                            gap: 4,
                            fontSize: 11,
                            color: "#999",
                            justifyContent: isUser ? "flex-end" : "flex-start",
                            paddingLeft: isUser ? 0 : 4,
                          }}
                        >
                          <ClockCircleOutlined style={{ fontSize: 10 }} />
                          <span>{new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}</span>
                        </div>
                      </div>

                      {isUser && (
                        <div
                          style={{
                            width: 36,
                            height: 36,
                            borderRadius: "50%",
                            background: "linear-gradient(135deg, #165DFF 0%, #4080FF 100%)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            flexShrink: 0,
                            boxShadow: "0 2px 8px rgba(22, 93, 255, 0.3)",
                          }}
                        >
                          <UserOutlined style={{ color: "#fff", fontSize: 16 }} />
                        </div>
                      )}
                    </div>

                    {showOptions && (
                      <div
                        style={{
                          maxWidth: "65%",
                          marginLeft: 46,
                          marginTop: 10,
                          display: "flex",
                          flexDirection: "column",
                          gap: 10,
                          animation: `fadeInUp 0.3s ease-out 0.1s both`,
                        }}
                      >
                        {msg.options!.map((opt, optIdx) => {
                          const isLastOption = optIdx === msg.options!.length - 1;
                          const shouldHighlight = msg.suggest_start && isLastOption;

                          return (
                            <Button
                              key={optIdx}
                              block
                              size="large"
                              variant={shouldHighlight ? "filled" : "outlined"}
                              style={{
                                textAlign: "left",
                                borderRadius: 16,
                                height: "auto",
                                padding: "10px 18px",
                                borderColor: shouldHighlight ? "#165DFF" : "#e0e0e0",
                                color: shouldHighlight ? "#165DFF" : "#555",
                                fontWeight: shouldHighlight ? 600 : 400,
                                background: shouldHighlight
                                  ? "linear-gradient(135deg, #e6f4ff 0%, #bae7ff 100%)"
                                  : "#fff",
                                boxShadow: shouldHighlight
                                  ? "0 2px 8px rgba(22, 93, 255, 0.15)"
                                  : "0 1px 3px rgba(0, 0, 0, 0.05)",
                                transition: "all 0.3s ease",
                                border: shouldHighlight ? "1px solid #165DFF" : "1px solid #e8e8e8",
                              }}
                              onMouseEnter={(e) => {
                                if (!shouldHighlight) {
                                  e.currentTarget.style.borderColor = "#165DFF";
                                  e.currentTarget.style.color = "#165DFF";
                                  e.currentTarget.style.background = "#f0f5ff";
                                  e.currentTarget.style.transform = "translateX(4px)";
                                  e.currentTarget.style.boxShadow = "0 2px 8px rgba(22, 93, 255, 0.15)";
                                }
                              }}
                              onMouseLeave={(e) => {
                                if (!shouldHighlight) {
                                  e.currentTarget.style.borderColor = "#e0e0e0";
                                  e.currentTarget.style.color = "#555";
                                  e.currentTarget.style.background = "#fff";
                                  e.currentTarget.style.transform = "translateX(0)";
                                  e.currentTarget.style.boxShadow = "0 1px 3px rgba(0, 0, 0, 0.05)";
                                }
                              }}
                              onClick={() => handleOptionClick(opt, msg.suggest_start)}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                {shouldHighlight && (
                                  <CheckCircleOutlined style={{ color: "#165DFF", fontSize: 16 }} />
                                )}
                                {!shouldHighlight && (
                                  <div
                                    style={{
                                      width: 6,
                                      height: 6,
                                      borderRadius: "50%",
                                      background: "#d9d9d9",
                                    }}
                                  />
                                )}
                                <span>{opt}</span>
                              </div>
                            </Button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
              {loading && (
                <div style={{ display: "flex", alignItems: "flex-end", gap: 10, marginBottom: 24 }}>
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: "50%",
                      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      boxShadow: "0 2px 8px rgba(102, 126, 234, 0.3)",
                    }}
                  >
                    <RobotOutlined style={{ color: "#fff", fontSize: 18 }} />
                  </div>
                  <div
                    style={{
                      padding: "14px 18px",
                      borderRadius: "18px 18px 18px 4px",
                      background: "linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)",
                      boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
                      border: "1px solid #e8e8e8",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Spin indicator={<LoadingOutlined style={{ fontSize: 14, color: "#165DFF" }} spin />} />
                      <span style={{ color: "#555", fontSize: 14 }}>AI正在思考...</span>
                    </div>
                    <div style={{ display: "flex", gap: 4, marginTop: 8 }}>
                      {[0, 1, 2].map((i) => (
                        <div
                          key={i}
                          style={{
                            width: 6,
                            height: 6,
                            borderRadius: "50%",
                            background: "#165DFF",
                            animation: `bounce 1.4s infinite ease-in-out`,
                            animationDelay: `${i * 0.16}s`,
                          }}
                        />
                      ))}
                    </div>
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
                  onClick={() => handleSend()}
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
                  onClick={() => handleDeleteHistory(item.id)}
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