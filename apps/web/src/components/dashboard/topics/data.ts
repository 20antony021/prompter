"use server";

import { auth } from "@clerk/nextjs/server";
import type { Topic } from "@/types/topic";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v2";

export async function getTopics(search?: string): Promise<Topic[]> {
  try {
    // 在服务端使用 auth() 获取 token
    const { getToken } = await auth();
    const token = await getToken();
    
    if (!token) {
      console.error("No token available");
      return [];
    }
    
    const endpoint = `${API_BASE_URL}/topics/${search?.trim() ? `?q=${encodeURIComponent(search.trim())}` : ""}`;
    const response = await fetch(endpoint, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });
    
    if (!response.ok) {
      console.error(`Failed to fetch topics: ${response.status} ${response.statusText}`);
      return [];
    }
    
    const raw = await response.json();
    if (!Array.isArray(raw)) return [];
    return raw.map((t: any) => ({
      id: t.id,
      name: t.name,
      logo: t.logo ?? undefined,
      description: t.description ?? undefined,
      isActive: typeof t.is_active === "boolean" ? t.is_active : !!t.isActive,
      createdAt: t.created_at ?? t.createdAt,
      updatedAt: t.updated_at ?? t.updatedAt,
      userId: t.user_id ?? t.userId,
      prompts: t.prompts,
    }));
  } catch (error) {
    console.error("Failed to fetch topics:", error);
    return [];
  }
}
