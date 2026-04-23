import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AuthGuard from "@/components/layout/AuthGuard";
import MainLayout from "@/components/layout/MainLayout";
import LoginPage from "@/pages/LoginPage";
import HomePage from "@/pages/HomePage";
import AppsListPage from "@/pages/AppsListPage";
import AppDetailPage from "@/pages/AppDetailPage";
import HistoryPage from "@/pages/HistoryPage";
import UserManagePage from "@/pages/admin/UserManagePage";
import TemplateManagePage from "@/pages/admin/TemplateManagePage";
import StatsPage from "@/pages/admin/StatsPage";
import ModelConfigPage from "@/pages/admin/ModelConfigPage";
import SkillsPage from "@/pages/SkillsPage";
import CreateAppPage from "@/pages/CreateAppPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <AuthGuard>
              <MainLayout />
            </AuthGuard>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="create" element={<CreateAppPage />} />
          <Route path="apps" element={<AppsListPage />} />
          <Route path="apps/:appId" element={<AppDetailPage />} />
          <Route path="skills" element={<SkillsPage />} />
          <Route
            path="history"
            element={
              <AuthGuard forbidAnnotator>
                <HistoryPage />
              </AuthGuard>
            }
          />

          {/* 管理员路由 */}
          <Route
            path="admin/users"
            element={
              <AuthGuard requireAdmin>
                <UserManagePage />
              </AuthGuard>
            }
          />
          <Route
            path="admin/template"
            element={
              <AuthGuard requireAdmin>
                <TemplateManagePage />
              </AuthGuard>
            }
          />
          <Route
            path="admin/stats"
            element={
              <AuthGuard requireAdmin>
                <StatsPage />
              </AuthGuard>
            }
          />
          <Route
            path="admin/models"
            element={
              <AuthGuard requireAdmin>
                <ModelConfigPage />
              </AuthGuard>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
