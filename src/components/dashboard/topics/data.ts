"use server";

import { db } from "@/db";
import { topics } from "@/db/schema";
import { eq, desc } from "drizzle-orm";
import { getUser } from "@/auth/server";
import type { Topic } from "@/types/topic";
import { cache } from "react";

export async function getTopics(): Promise<Topic[]> {
  const user = await getUser();
  console.log("Fetching topics for user:", user?.id);
  if (!user) throw new Error("User not found");

  try {
    const res = await db.query.topics.findMany({
      where: eq(topics.userId, user.id),
      orderBy: desc(topics.createdAt),
      with: {
        prompts: true,
      },
    });

    return res;
  } catch (error) {
    console.error("Failed to fetch topics:", error);
    return [];
  }
}

// Optimized version for select dropdowns - only fetches essential fields without prompts
export const getTopicsForSelect = cache(async (): Promise<Pick<Topic, 'id' | 'name' | 'logo' | 'description'>[]> => {
  const user = await getUser();
  if (!user) throw new Error("User not found");

  try {
    const res = await db
      .select({
        id: topics.id,
        name: topics.name,
        logo: topics.logo,
        description: topics.description,
      })
      .from(topics)
      .where(eq(topics.userId, user.id))
      .orderBy(desc(topics.createdAt));

    return res;
  } catch (error) {
    console.error("Failed to fetch topics for select:", error);
    return [];
  }
});
