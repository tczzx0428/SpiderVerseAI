import client from "./client";

export interface AICreation {
  id: number;
  title: string | null;
  status: "chatting" | "generating" | "building" | "running" | "failed" | "cancelled";
  progress: number;
  progress_message: string | null;
  error_message: string | null;
  app_id: number | null;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  options?: string[];
  suggest_start?: boolean;
}

export interface ChatResponse {
  reply: string;
  conversation: ChatMessage[];
  options: string[];
  suggest_start: boolean;
}

export const createNewSession = (title?: string) =>
  client.post<AICreation>("/ai-create/new", null, { params: { title } });

export const sendMessage = (creationId: number, message: string) =>
  client.post<ChatResponse>("/ai-create/chat", {
    creation_id: creationId,
    message,
  });

export const startCreation = (creationId: number) =>
  client.post("/ai-create/start", { creation_id: creationId });

export const getCreationStatus = (creationId: number) =>
  client.get<AICreation>(`/ai-create/${creationId}`);

export const listCreations = (limit = 20) =>
  client.get<AICreation[]>("/ai-create", { params: { limit } });

export const deleteCreation = (creationId: number) =>
  client.delete(`/ai-create/${creationId}`);