import { Topic, Prompt } from "@/types/topic";
import { defaultApiClient } from "./client";

export async function getTopics(): Promise<Topic[]> {
  const response = await defaultApiClient.get("/topics/");

  if (!response.ok) {
    throw new Error("Failed to fetch topics");
  }

  return response.json();
}

export async function getTopic(topicId: string): Promise<Topic> {
  const response = await defaultApiClient.get(`/topics/${topicId}`);

  if (!response.ok) {
    throw new Error("Failed to fetch topic");
  }

  return response.json();
}

export async function createTopic(data: {
  name: string;
  logo?: string;
  description?: string;
}): Promise<Topic> {
  const response = await defaultApiClient.post("/topics/", data);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create topic");
  }

  return response.json();
}

export async function createTopicFromUrl(url: string): Promise<Topic> {
  const response = await defaultApiClient.post("/topics/from-url", { url });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create topic");
  }

  return response.json();
}

export async function updateTopic(
  topicId: string,
  data: Partial<Topic>
): Promise<Topic> {
  const response = await defaultApiClient.patch(`/topics/${topicId}`, data);

  if (!response.ok) {
    throw new Error("Failed to update topic");
  }

  return response.json();
}

export async function deleteTopic(topicId: string): Promise<void> {
  const response = await defaultApiClient.delete(`/topics/${topicId}`);

  if (!response.ok) {
    throw new Error("Failed to delete topic");
  }
}

export async function getTopicPrompts(topicId: string): Promise<Prompt[]> {
  const response = await defaultApiClient.get(`/topics/${topicId}/prompts`);

  if (!response.ok) {
    throw new Error("Failed to fetch prompts");
  }

  return response.json();
}
