import { auth, clerkClient } from "@clerk/nextjs/server";
import { db } from "@/db";
import { user as userTable } from "@/db/schema";
import { eq } from "drizzle-orm";
import { cache } from "react";

export type User = {
  id: string;
  name: string;
  email: string;
  emailVerified: boolean;
  image?: string | null;
  createdAt: Date;
  updatedAt: Date;
  stripeCustomerId?: string | null;
  stripeSubscriptionId?: string | null;
  stripePriceId?: string | null;
  stripeCurrentPeriodEnd?: Date | null;
  plan: "free" | "basic" | "pro" | "enterprise";
  planStatus: string;
};

// Use getToken instead of userId to avoid headers() iteration error
export const getUser = cache(async (): Promise<User | null> => {
  try {
    const { getToken, userId: syncUserId } = await auth();

    // For API routes and server actions, prefer getToken
    const token = await getToken();
    if (!token) {
      return null;
    }

    // Extract userId from token payload
    const userId = syncUserId;
    if (!userId) {
      return null;
    }

    // Check if user exists in our database
    const existingUsers = await db
      .select()
      .from(userTable)
      .where(eq(userTable.id, userId))
      .limit(1);

    let dbUser = existingUsers[0];

    // If user doesn't exist in database, create them
    if (!dbUser) {
      // Get user data from Clerk
      const clerkUser = await clerkClient.users.getUser(userId);
      const email =
        clerkUser.emailAddresses[0]?.emailAddress || `${userId}@clerk.user`;

      // Check if user exists by email (from previous auth system)
      const existingByEmail = await db
        .select()
        .from(userTable)
        .where(eq(userTable.email, email))
        .limit(1);

      if (existingByEmail[0]) {
        // Update existing user's ID to match Clerk userId
        const updatedUsers = await db
          .update(userTable)
          .set({
            id: userId,
            name: clerkUser.fullName || clerkUser.username || "User",
            emailVerified:
              clerkUser.emailAddresses[0]?.verification?.status === "verified",
            image: clerkUser.imageUrl,
            updatedAt: new Date(),
          })
          .where(eq(userTable.email, email))
          .returning();

        dbUser = updatedUsers[0];
      } else {
        // Create new user
        const newUsers = await db
          .insert(userTable)
          .values({
            id: userId,
            name: clerkUser.fullName || clerkUser.username || "User",
            email,
            emailVerified:
              clerkUser.emailAddresses[0]?.verification?.status === "verified",
            image: clerkUser.imageUrl,
            plan: "free",
            planStatus: "active",
          })
          .returning();

        dbUser = newUsers[0];
      }
    }

    return dbUser || null;
  } catch (error) {
    console.error("Failed to get user:", error);
    return null;
  }
});
