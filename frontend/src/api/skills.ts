import client from "./client";

export interface SkillFile {
  name: string;
  size: number;
}

export interface Skill {
  name: string;
  content: string;
  description: string;
  category: string;
  author_id: number | null;
  author_name: string;
  downloads: number;
  pinned: boolean;
  favorited: boolean;
  version: string;
  changelog: string;
  files: SkillFile[];
  created_at: string | null;
  updated_at: string | null;
  ups: number;
  downs: number;
  my_vote: "up" | "down" | "none";
  has_update: boolean;
}

export interface SkillComment {
  user_id: number;
  user_name: string;
  content: string;
  created_at: string;
}

export interface SkillCategory {
  value: string;
  label: string;
}

export const listSkills = (q?: string, category?: string, sort?: string, favoritesOnly?: boolean) => {
  const params: Record<string, string> = {};
  if (q) params.q = q;
  if (category) params.category = category;
  if (sort) params.sort = sort;
  if (favoritesOnly) params.favorites_only = "true";
  return client.get<Skill[]>("/skills", { params });
};

export const getSkill = (name: string) =>
  client.get<Skill>(`/skills/${name}`);

export const createSkill = (data: FormData) =>
  client.post<Skill>("/skills", data, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const updateSkill = (name: string, data: FormData) =>
  client.put<Skill>(`/skills/${name}`, data, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const deleteSkill = (name: string) =>
  client.delete(`/skills/${name}`);

export const downloadSkill = (name: string) =>
  client.get(`/skills/${name}/download`, { responseType: "blob" });

export const pinSkill = (name: string, pinned: boolean) =>
  client.put<Skill>(`/skills/${name}/pin`, { pinned });

export const toggleFavorite = (name: string, favorite: boolean) =>
  client.put<{ name: string; favorited: boolean }>(`/skills/${name}/favorite`, { favorite });

export const listCategories = () =>
  client.get<SkillCategory[]>("/skills/categories");

export interface SkillStats {
  total_skills: number;
  total_downloads: number;
  category_breakdown: Record<string, number>;
  top_downloaded: { name: string; downloads: number }[];
  top_authors: { name: string; count: number }[];
}

export const getSkillStats = () =>
  client.get<SkillStats>("/skills/stats/overview");

export const previewFile = (skillName: string, filePath: string) =>
  client.get<{ name: string; content: string }>(`/skills/${skillName}/files/${filePath}`);

export const voteSkill = (name: string, vote: "up" | "down" | "none") =>
  client.put<{ name: string; ups: number; downs: number; my_vote: string }>(`/skills/${name}/vote`, { vote });

export const listComments = (name: string) =>
  client.get<SkillComment[]>(`/skills/${name}/comments`);

export const addComment = (name: string, content: string) =>
  client.post<SkillComment[]>(`/skills/${name}/comments`, { content });

export const deleteComment = (name: string, index: number) =>
  client.delete<SkillComment[]>(`/skills/${name}/comments/${index}`);
