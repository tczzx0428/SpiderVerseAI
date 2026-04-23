import { useState, useEffect } from "react";
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Space,
  Tag,
  Typography,
  message,
  Popconfirm,
  Tooltip,
  Empty,
  Spin,
  InputNumber,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import {
  listModels,
  getProviders,
  createModel,
  updateModel,
  deleteModel,
  toggleModel,
  type AIModelConfig,
  type ModelProvider,
} from "@/api/modelConfig";

const { Title, Text } = Typography;
const { TextArea } = Input;

export default function ModelConfigPage() {
  const [models, setModels] = useState<AIModelConfig[]>([]);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<AIModelConfig | null>(null);
  const [form] = Form.useForm();
  const [selectedProvider, setSelectedProvider] = useState("deepseek");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [modelsRes, providersRes] = await Promise.all([
        listModels(),
        getProviders(),
      ]);
      setModels(modelsRes.data);
      setProviders(providersRes.data);
    } catch (e: any) {
      message.error("加载失败");
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingModel(null);
    form.resetFields();
    form.setFieldsValue({
      provider: "deepseek",
      base_url: "https://api.deepseek.com/v1",
      model_id: "deepseek-chat",
      usage: "both",
      is_enabled: true,
      priority: 0,
    });
    setSelectedProvider("deepseek");
    setModalOpen(true);
  };

  const handleEdit = (record: AIModelConfig) => {
    setEditingModel(record);
    form.setFieldsValue(record);
    setSelectedProvider(record.provider || "custom");
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingModel) {
        await updateModel(editingModel.id, values);
        message.success("更新成功");
      } else {
        await createModel(values as any);
        message.success("创建成功");
      }
      setModalOpen(false);
      loadData();
    } catch (e: any) {
      if (e?.errorFields) return;
      message.error(e.response?.data?.detail || "操作失败");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteModel(id);
      message.success("删除成功");
      loadData();
    } catch {
      message.error("删除失败");
    }
  };

  const handleToggle = async (id: number) => {
    try {
      await toggleModel(id);
      loadData();
    } catch {
      message.error("切换状态失败");
    }
  };

  const currentProvider = providers.find((p) => p.id === selectedProvider);

  const columns = [
    {
      title: "名称",
      dataIndex: "name",
      key: "name",
      render: (text: string, record: AIModelConfig) => (
        <Space>
          <Text strong>{text}</Text>
          <Tag color={getProviderColor(record.provider)}>{getProviderName(record.provider)}</Tag>
        </Space>
      ),
    },
    {
      title: "模型",
      dataIndex: "model_id",
      key: "model_id",
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: "API地址",
      dataIndex: "base_url",
      key: "base_url",
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text type="secondary">{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: "API Key",
      dataIndex: "api_key",
      key: "api_key",
      render: (text: string) => (
        <Text code style={{ fontSize: 12 }}>{text}</Text>
      ),
    },
    {
      title: "用途",
      dataIndex: "usage",
      key: "usage",
      width: 100,
      render: (usage: string) => {
        const map: Record<string, { color: string; label: string }> = {
          chat: { color: "blue", label: "对话" },
          code: { color: "green", label: "代码" },
          both: { color: "purple", label: "两者" },
        };
        const item = map[usage] || map.chat;
        return <Tag color={item.color}>{item.label}</Tag>;
      },
    },
    {
      title: "状态",
      dataIndex: "is_enabled",
      key: "is_enabled",
      width: 80,
      render: (enabled: boolean, record: AIModelConfig) => (
        <Switch
          checked={enabled}
          onChange={() => handleToggle(record.id)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          size="small"
        />
      ),
    },
    {
      title: "优先级",
      dataIndex: "priority",
      key: "priority",
      width: 70,
      sorter: (a: AIModelConfig, b: AIModelConfig) => a.priority - b.priority,
    },
    {
      title: "操作",
      key: "action",
      width: 120,
      render: (_: any, record: AIModelConfig) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确认删除此模型配置？" onConfirm={() => handleDelete(record.id)} okText="删除" cancelText="取消">
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <SettingOutlined style={{ marginRight: 8 }} />模型配置
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>添加模型</Button>
      </div>

      <Card title="快速添加预设模型" style={{ marginBottom: 16 }} size="small">
        <Space wrap size="middle">
          {providers.map((p) => (
            <Card
              key={p.id}
              size="small"
              hoverable
              style={{ width: 180 }}
              onClick={() => {
                setEditingModel(null);
                form.resetFields();
                form.setFieldsValue({
                  provider: p.id,
                  base_url: p.base_url,
                  usage: "both",
                  is_enabled: true,
                  priority: models.length,
                });
                setSelectedProvider(p.id);
                if (p.models.length > 0) {
                  form.setFieldsValue({ model_id: p.models[0].id });
                }
                setModalOpen(true);
              }}
            >
              <Space direction="vertical" size={4} style={{ width: "100%" }}>
                <Text strong>{p.name}</Text>
                {p.models.length > 0 && (
                  <Text type="secondary" style={{ fontSize: 12 }}>支持 {p.models.length} 个模型</Text>
                )}
              </Space>
            </Card>
          ))}
        </Space>
      </Card>

      <Card>
        <Table
          dataSource={models}
          columns={columns}
          rowKey="id"
          loading={loading}
          locale={{ emptyText: <Empty description="暂无模型配置，点击上方快速添加" /> }}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingModel ? "编辑模型配置" : "添加模型"}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="保存"
        cancelText="取消"
        width={560}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label="显示名称" name="name" rules={[{ required: true, message: "请输入名称" }]}>
            <Input placeholder="如：DeepSeek Chat、GPT-4o" />
          </Form.Item>

          <Form.Item label="提供商" name="provider">
            <Select onChange={(val) => {
              setSelectedProvider(val);
              const provider = providers.find((p) => p.id === val);
              if (provider) {
                form.setFieldsValue({ base_url: provider.base_url });
                if (provider.models.length > 0 && !editingModel) {
                  form.setFieldsValue({ model_id: provider.models[0].id });
                }
              }
            }}>
              {providers.map((p) => (<Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>))}
            </Select>
          </Form.Item>

          {currentProvider && currentProvider.models.length > 0 && (
            <Form.Item label="选择模型" name="model_id">
              <Select>
                {currentProvider.models.map((m) => (<Select.Option key={m.id} value={m.id}>{m.name}</Select.Option>))}
              </Select>
            </Form.Item>
          )}

          {(selectedProvider === "custom" || !currentProvider || currentProvider.models.length === 0) && (
            <Form.Item label="模型ID" name="model_id" rules={[{ required: true, message: "请输入模型ID" }]}>
              <Input placeholder="如：deepseek-chat、gpt-4o" />
            </Form.Item>
          )}

          <Form.Item label="API Base URL" name="base_url" rules={[{ required: true, message: "请输入API地址" }]}>
            <Input placeholder="https://api.deepseek.com/v1" />
          </Form.Item>

          <Form.Item label="API Key" name="api_key" rules={[{ required: true, message: "请输入API Key" }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>

          <Form.Item label="用途" name="usage">
            <Select>
              <Select.Option value="chat">仅对话（用于AI聊天）</Select.Option>
              <Select.Option value="code">仅代码生成</Select.Option>
              <Select.Option value="both">两者都支持</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="优先级" name="priority" tooltip="数字越小优先级越高">
            <InputNumber min={0} max={100} style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item label="描述说明" name="description">
            <TextArea rows={2} placeholder="可选：描述此模型的用途" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

function getProviderColor(provider: string): string {
  const colors: Record<string, string> = { deepseek: "blue", openai: "green", zhipu: "purple", qwen: "orange", custom: "default" };
  return colors[provider] || "default";
}

function getProviderName(provider: string): string {
  const names: Record<string, string> = { deepseek: "DeepSeek", openai: "OpenAI", zhipu: "智谱AI", qwen: "通义千问", custom: "自定义" };
  return names[provider] || provider;
}