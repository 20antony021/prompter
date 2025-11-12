export interface Topic {
  id: string;
  name: string;
  logo?: string;
  description?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  userId: string;
  prompts?: Prompt[];
}

export interface Prompt {
  id: string;
  content: string;
  topicId: string;
  userId: string;
  status: "pending" | "processing" | "completed" | "failed" | "cancelled";
  geoRegion: string;
  visibilityScore?: number;
  tags: string[];
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface TopicSuggestion {
  id: string;
  name: string;
  description: string;
  category: string;
}
