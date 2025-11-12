import { db } from "@/db";
import { prompts, topics } from "@/db/schema";
import { eq, and, count, gte } from "drizzle-orm";
import { isPlanType, PLANS, PlanType } from "./stripe/server";
import { getUser } from "@/auth/server";
import { checkUserSubscriptionExpired } from "./subscription/check-expired";

export interface UserSubscription {
  plan: PlanType;
  planStatus: string;
  stripeCustomerId: string | null;
  stripeSubscriptionId: string | null;
  stripeCurrentPeriodEnd: Date | null;
  limits: (typeof PLANS)[PlanType]["limits"];
}

const getUserPlan = async (): Promise<UserSubscription> => {
  const user = await getUser();
  const plan = user?.plan && isPlanType(user.plan) ? user.plan : "free";
  const subDetails = PLANS[plan] ?? PLANS.free;

  // Check if subscription has expired (safety check in case webhooks failed)
  if (user?.id && user.plan !== "free") {
    await checkUserSubscriptionExpired(user.id);

    // Refetch user data in case it was updated
    const updatedUser = await getUser();
    const updatedPlan =
      updatedUser?.plan && isPlanType(updatedUser.plan)
        ? updatedUser.plan
        : "free";
    const updatedSubDetails = PLANS[updatedPlan] ?? PLANS.free;

    return {
      plan: updatedPlan,
      planStatus: updatedUser?.planStatus || "active",
      stripeCustomerId: updatedUser?.stripeCustomerId ?? null,
      stripeSubscriptionId: updatedUser?.stripeSubscriptionId ?? null,
      stripeCurrentPeriodEnd: updatedUser?.stripeCurrentPeriodEnd ?? null,
      limits: updatedSubDetails.limits,
    };
  }

  return {
    plan,
    planStatus: user?.planStatus || "active",
    stripeCustomerId: user?.stripeCustomerId ?? null,
    stripeSubscriptionId: user?.stripeSubscriptionId ?? null,
    stripeCurrentPeriodEnd: user?.stripeCurrentPeriodEnd ?? null,
    limits: subDetails.limits,
  };
};

export async function checkUsageLimit(userId: string): Promise<{
  canProcess: boolean;
  currentUsage: number;
  limit: number;
  plan: PlanType;
}> {
  const user = await getUser();

  if (!user) {
    return {
      canProcess: false,
      currentUsage: 0,
      limit: 0,
      plan: "free",
    };
  }

  const userPlan = await getUserPlan();

  if (user.planStatus !== "active") {
    return {
      canProcess: false,
      currentUsage: 0,
      limit: userPlan.limits.promptsPerDay,
      plan: userPlan.plan,
    };
  }

  // Get today's date at 00:00:00 in UTC
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);

  // Count prompts created today only
  const [usage] = await db
    .select({ count: count() })
    .from(prompts)
    .where(and(
      eq(prompts.userId, userId),
      gte(prompts.createdAt, today)
    ));

  const currentUsage = usage?.count ?? 0;
  const limit = userPlan.limits.promptsPerDay;

  return {
    canProcess: currentUsage <= limit,
    currentUsage,
    limit,
    plan: userPlan.plan,
  };
}

export async function getAvailableProviders(): Promise<string[]> {
  const user = await getUser();

  if (!user || user.planStatus !== "active") {
    return [...PLANS.free.limits.providers];
  }

  const userPlan = await getUserPlan();

  return [...userPlan.limits.providers];
}

export function getProcessingPriority(plan: PlanType) {
  return PLANS[plan].limits.priority;
}

export async function checkTopicLimit(userId: string): Promise<{
  canCreateTopic: boolean;
  currentTopics: number;
  limit: number;
  plan: PlanType;
}> {
  const user = await getUser();

  if (!user) {
    return {
      canCreateTopic: false,
      currentTopics: 0,
      limit: 0,
      plan: "free",
    };
  }

  const userPlan = await getUserPlan();

  if (user.planStatus !== "active") {
    return {
      canCreateTopic: false,
      currentTopics: 0,
      limit: userPlan.limits.topicsLimit,
      plan: userPlan.plan,
    };
  }

  // Get today's date at 00:00:00 in UTC
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);

  // Count topics created today only
  const [topicCount] = await db
    .select({ count: count() })
    .from(topics)
    .where(and(
      eq(topics.userId, userId),
      gte(topics.createdAt, today)
    ));

  const currentTopics = topicCount?.count || 0;
  const limit = userPlan.limits.topicsLimit;

  return {
    canCreateTopic: currentTopics < limit,
    currentTopics,
    limit,
    plan: userPlan.plan,
  };
}
