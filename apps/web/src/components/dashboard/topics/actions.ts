"use server";

import { revalidatePath } from "next/cache";
import { auth } from "@clerk/nextjs/server";
import type { Topic } from "@/types/topic";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v2";

export async function deleteTopic(topicId: string) {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    
    if (!token) {
      return {
        success: false,
        error: "Not authenticated",
      };
    }

    const response = await fetch(`${API_BASE_URL}/topics/${topicId}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete topic: ${response.statusText}`);
    }
    
    revalidatePath("/dashboard/topics");
  } catch (error) {
    console.error("Failed to delete topic:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error occurred",
    };
  }
}

export interface CreateTopicFromUrlData {
  url: string;
}

export interface CreateTopicState {
  success?: boolean;
  error?: string;
  topicId?: string;
}

export async function createTopicFromUrl(
  prevState: CreateTopicState | null,
  formData: FormData
): Promise<CreateTopicState> {
  try {
    const url = formData.get("url") as string;

    if (!url?.trim()) {
      return {
        success: false,
        error: "URL is required",
      };
    }
    
    const { getToken } = await auth();
    const token = await getToken();
    
    if (!token) {
      return {
        success: false,
        error: "Not authenticated",
      };
    }
    
    const response = await fetch(`${API_BASE_URL}/topics/from-url`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: url.trim() }),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to create topic");
    }
    
    const topic: Topic = await response.json();

    revalidatePath("/dashboard/topics");

    return {
      success: true,
      topicId: topic.id,
    };
  } catch (error) {
    console.error("Failed to create topic:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error occurred",
    };
  }
}

// Wrapper used by the suggestions dialog <form action={...}>
export async function createTopicFromSuggestion(formData: FormData): Promise<void> {
  try {
    const name = (formData.get("name") as string)?.trim();
    const description = (formData.get("description") as string)?.trim();
    const logo = (formData.get("logo") as string)?.trim();

    if (!name) return;

    const { getToken } = await auth();
    const token = await getToken();
    if (!token) return;

    const res = await fetch(`${API_BASE_URL}/topics/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, description, logo }),
    });

    if (!res.ok) {
      console.error("Failed to create topic from suggestion", await res.text());
    }

    revalidatePath("/dashboard/topics");
  } catch (e) {
    console.error("createTopicFromSuggestion error", e);
  }
}
