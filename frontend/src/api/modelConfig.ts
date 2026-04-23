import client from "./client";

export interface AIModelConfig {
  id: number;
  name: string;
  provider: string;
  model_id: string;
  api_key: string;
  base_url: string;
  usage: "chat" | "code" | "both";
  is_enabled: boolean;
  priority: number;
  description: string | null;
  system_prompt: string | null;
  created_by: number;
  created_at: string;
}

export interface ModelProvider {
  id: string;
  name: string;
  base_url: string;
  models: { id: string; name: string }[];
}

export const listModels = (enabledOnly = false) =>
  client.get<AIModelConfig[]>("/admin/models", { params: { enabled_only: enabledOnly } });

export const getProviders = () =>
  client.get<ModelProvider[]>("/admin/models/providers");

export const createModel = (data: Partial<AIModelConfig> & { name: string; api_key: string; base_url: string }) =>
  client.post<AIModelConfig>("/admin/models", data);

export const updateModel = (id: number, data: Partial<AIModelConfig>) =>
  client.put<AIModelConfig>(`/admin/models/${id}`, data);

export const deleteModel = (id: number) =>
  client.delete(`/admin/models/${id}`);

export const toggleModel = (id: number) =>
  client.post<AIModelConfig>(`/admin/models/${id}/toggle`);

export const getSystemPrompt = (id: number) =>
  client.get<{ id: number; name: string; system_prompt: string }>(`/admin/models/${id}/system-prompt`);

export const updateSystemPrompt = (id: number, system_prompt: string) =>
  client.put<{ id: number; name: string; system_prompt: string; message: string }>(`/admin/models/${id}/system-prompt`, { system_prompt });