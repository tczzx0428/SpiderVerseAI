import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { Form, Input, Modal, message } from "antd";
import { useState } from "react";
import {
  HomeOutlined,
  AppstoreOutlined,
  HistoryOutlined,
  UserOutlined,
  FileTextOutlined,
  BarChartOutlined,
  LockOutlined,
  LogoutOutlined,
  ThunderboltOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import { logout, changePassword } from "@/api/auth";

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearAuth } = useAuthStore();
  const [pwModalOpen, setPwModalOpen] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [form] = Form.useForm();

  const isActive = (path: string) =>
    path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);

  const isAdmin = user?.role === "admin";
  const isAnnotator = user?.role === "annotator";

  const navItems = [
    { path: "/", icon: <HomeOutlined />, label: "首页" },
    { path: "/create", icon: <RobotOutlined />, label: "创作应用" },
    { path: "/apps", icon: <AppstoreOutlined />, label: "应用管理" },
    { path: "/skills", icon: <ThunderboltOutlined />, label: "Skills 市场" },
    ...(!isAnnotator ? [{ path: "/history", icon: <HistoryOutlined />, label: "历史记录" }] : []),
  ];

  const adminMenuItems = [
    { path: "/admin/users", icon: <UserOutlined />, label: "用户管理" },
    { path: "/admin/template", icon: <FileTextOutlined />, label: "代码规范Prompt" },
    { path: "/admin/stats", icon: <BarChartOutlined />, label: "使用统计" },
  ];

  const roleLabel: Record<string, string> = {
    admin: "管理员",
    user: "普通用户",
    annotator: "标注账号",
  };

  const handleChangePassword = async () => {
    const values = await form.validateFields();
    if (values.new_password !== values.confirm_password) {
      form.setFields([{ name: "confirm_password", errors: ["两次密码不一致"] }]);
      return;
    }
    setPwLoading(true);
    try {
      await changePassword(values.old_password, values.new_password);
      message.success("密码修改成功");
      setPwModalOpen(false);
      form.resetFields();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "修改失败");
    } finally {
      setPwLoading(false);
    }
  };

  const handleLogout = async () => {
    try { await logout(); } catch { /* ignore */ }
    clearAuth();
    navigate("/login");
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#fafafa" }}>
      {/* 侧边栏 */}
      <aside style={{
        position: "fixed", left: 0, top: 0,
        width: 240, height: "100vh",
        background: "#ffffff",
        borderRight: "1px solid #e5e5e5",
        display: "flex", flexDirection: "column",
        zIndex: 100,
      }}>
        {/* Logo */}
        <div style={{ padding: "32px 24px", borderBottom: "1px solid #f0f0f0" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              width: 40, height: 40,
              background: "#2c2c2c", borderRadius: 8,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 14, fontWeight: 700, color: "#fff", letterSpacing: "-0.5px",
            }}>PT</div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#1a1a1a" }}>PulseTeach AI</div>
              <div style={{ fontSize: 11, color: "#999", letterSpacing: "0.3px" }}>律动课堂</div>
            </div>
          </div>
        </div>

        {/* 导航 */}
        <nav style={{ flex: 1, padding: "16px 12px", overflow: "hidden" }}>
          {[
            ...navItems,
            ...(isAdmin ? [null, ...adminMenuItems] : []),
          ].map((item, idx) => {
            if (item === null) {
              return (
                <div key="divider" style={{
                  borderTop: "1px solid #f0f0f0",
                  margin: "8px 4px 8px",
                }} />
              );
            }
            const active = isActive(item.path);
            return (
              <div
                key={item.path}
                onClick={() => navigate(item.path)}
                style={{
                  display: "flex", alignItems: "center", gap: 12,
                  padding: "12px 16px", marginBottom: 4,
                  borderRadius: 8, fontSize: 14, fontWeight: active ? 600 : 500,
                  color: active ? "#1a1a1a" : "#666",
                  background: active ? "#f0f0f0" : "transparent",
                  cursor: "pointer", transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  if (!active) (e.currentTarget as HTMLElement).style.background = "#f7f7f7";
                }}
                onMouseLeave={(e) => {
                  if (!active) (e.currentTarget as HTMLElement).style.background = "transparent";
                }}
              >
                <span style={{ fontSize: 18, display: "flex", alignItems: "center", color: active ? "#165DFF" : "#86909C" }}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
            );
          })}
        </nav>

        {/* 用户信息 */}
        <div style={{ padding: "16px 24px 20px", borderTop: "1px solid #f0f0f0" }}>
          {/* 用户头像 + 名称 */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
            <div style={{
              width: 36, height: 36, borderRadius: "50%",
              background: "linear-gradient(135deg, #2c2c2c, #1a1a1a)",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "#fff", fontSize: 14, fontWeight: 600, flexShrink: 0,
            }}>
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#1a1a1a" }}>{user?.username}</div>
              <div style={{ fontSize: 11, color: "#999" }}>
                {roleLabel[user?.role ?? "user"] ?? user?.role}
              </div>
            </div>
          </div>

          {/* 操作按钮行 */}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => setPwModalOpen(true)}
              style={{
                flex: 1, padding: "6px 0",
                display: "flex", alignItems: "center", justifyContent: "center", gap: 4,
                background: "#f7f7f7", color: "#555",
                border: "1px solid #e5e5e5", borderRadius: 6,
                fontSize: 12, cursor: "pointer", transition: "all 0.15s",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#efefef"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "#f7f7f7"; }}
              title="修改密码"
            >
              <LockOutlined style={{ fontSize: 12 }} />
              修改密码
            </button>
            <button
              onClick={() => Modal.confirm({
                title: "确认退出登录？",
                okText: "退出",
                cancelText: "取消",
                onOk: handleLogout,
              })}
              style={{
                flex: 1, padding: "6px 0",
                display: "flex", alignItems: "center", justifyContent: "center", gap: 4,
                background: "#f7f7f7", color: "#555",
                border: "1px solid #e5e5e5", borderRadius: 6,
                fontSize: 12, cursor: "pointer", transition: "all 0.15s",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#efefef"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "#f7f7f7"; }}
              title="退出登录"
            >
              <LogoutOutlined style={{ fontSize: 12 }} />
              退出登录
            </button>
          </div>
        </div>
      </aside>

      {/* 主内容 */}
      <main style={{ marginLeft: 240, flex: 1, padding: "0 48px 80px", minHeight: "100vh" }}>
        <Outlet />
      </main>

      {/* 修改密码弹窗 */}
      <Modal
        title="修改密码"
        open={pwModalOpen}
        onCancel={() => { setPwModalOpen(false); form.resetFields(); }}
        onOk={handleChangePassword}
        okText="确认修改"
        cancelText="取消"
        confirmLoading={pwLoading}
        width={400}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            label="原密码"
            name="old_password"
            rules={[{ required: true, message: "请输入原密码" }]}
          >
            <Input.Password placeholder="请输入原密码" />
          </Form.Item>
          <Form.Item
            label="新密码"
            name="new_password"
            rules={[
              { required: true, message: "请输入新密码" },
              { min: 6, message: "密码至少 6 位" },
            ]}
          >
            <Input.Password placeholder="请输入新密码（至少 6 位）" />
          </Form.Item>
          <Form.Item
            label="确认新密码"
            name="confirm_password"
            rules={[{ required: true, message: "请再次输入新密码" }]}
          >
            <Input.Password placeholder="再次输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
