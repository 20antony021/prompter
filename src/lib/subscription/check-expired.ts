import { db } from "@/db";
import { user } from "@/db/schema";
import { and, eq, lt, not, isNotNull } from "drizzle-orm";
import { stripe } from "@/lib/stripe/server";

/**
 * Check if a user's subscription has expired based on stripeCurrentPeriodEnd
 * This is a safety mechanism in case webhooks fail or are delayed
 */
export async function checkUserSubscriptionExpired(
  userId: string
): Promise<boolean> {
  const users = await db
    .select({
      stripeCurrentPeriodEnd: user.stripeCurrentPeriodEnd,
      stripeSubscriptionId: user.stripeSubscriptionId,
      plan: user.plan,
      planStatus: user.planStatus,
    })
    .from(user)
    .where(eq(user.id, userId))
    .limit(1);

  const currentUser = users[0];
  if (!currentUser) return false;

  // If user is on free plan, nothing to check
  if (currentUser.plan === "free") return false;

  // If no period end date, something is wrong, but don't auto-downgrade
  if (!currentUser.stripeCurrentPeriodEnd) return false;

  const now = new Date();
  const periodEnd = new Date(currentUser.stripeCurrentPeriodEnd);

  // Check if subscription has expired
  if (periodEnd < now && currentUser.planStatus !== "canceled") {
    console.log(
      `Subscription expired for user ${userId} (period ended: ${periodEnd.toISOString()})`
    );

    // Double-check with Stripe before downgrading
    if (currentUser.stripeSubscriptionId) {
      try {
        const subscription = await stripe.subscriptions.retrieve(
          currentUser.stripeSubscriptionId
        );

        // If Stripe says it's still active, update our database
        if (subscription.status === "active") {
          console.log(
            `Stripe subscription is still active, updating local database for user ${userId}`
          );

          await db
            .update(user)
            .set({
              stripeCurrentPeriodEnd: new Date(
                subscription.current_period_end * 1000
              ),
              planStatus: "active",
              updatedAt: new Date(),
            })
            .where(eq(user.id, userId));

          return false;
        }

        // Stripe confirms it's not active, downgrade to free
        console.log(
          `Stripe subscription is ${subscription.status}, downgrading user ${userId} to free`
        );
      } catch (error) {
        console.error(
          `Error checking Stripe subscription for user ${userId}:`,
          error
        );
        // If we can't verify with Stripe, don't auto-downgrade to be safe
        return false;
      }
    }

    // Downgrade user to free plan
    await db
      .update(user)
      .set({
        plan: "free",
        planStatus: "expired",
        stripeSubscriptionId: null,
        stripePriceId: null,
        updatedAt: new Date(),
      })
      .where(eq(user.id, userId));

    return true;
  }

  return false;
}

/**
 * Check all users with expired subscriptions and downgrade them
 * This should be run periodically (e.g., daily via cron job)
 */
export async function checkAllExpiredSubscriptions(): Promise<{
  checked: number;
  expired: number;
  errors: number;
}> {
  console.log("Starting expired subscriptions check...");

  const now = new Date();

  // Find all users with:
  // 1. A paid plan (not free)
  // 2. A period end date that has passed
  // 3. Not already marked as canceled/expired
  const expiredUsers = await db
    .select({
      id: user.id,
      email: user.email,
      plan: user.plan,
      stripeCustomerId: user.stripeCustomerId,
      stripeSubscriptionId: user.stripeSubscriptionId,
      stripeCurrentPeriodEnd: user.stripeCurrentPeriodEnd,
      planStatus: user.planStatus,
    })
    .from(user)
    .where(
      and(
        not(eq(user.plan, "free")),
        isNotNull(user.stripeCurrentPeriodEnd),
        lt(user.stripeCurrentPeriodEnd, now),
        not(eq(user.planStatus, "canceled")),
        not(eq(user.planStatus, "expired"))
      )
    );

  console.log(`Found ${expiredUsers.length} potentially expired subscriptions`);

  let expiredCount = 0;
  let errorCount = 0;

  for (const expiredUser of expiredUsers) {
    try {
      // Verify with Stripe before downgrading
      if (expiredUser.stripeSubscriptionId) {
        try {
          const subscription = await stripe.subscriptions.retrieve(
            expiredUser.stripeSubscriptionId
          );

          // If Stripe says it's still active, update our database
          if (subscription.status === "active") {
            console.log(
              `User ${expiredUser.email} subscription is still active in Stripe, updating local data`
            );

            await db
              .update(user)
              .set({
                stripeCurrentPeriodEnd: new Date(
                  subscription.current_period_end * 1000
                ),
                planStatus: "active",
                updatedAt: new Date(),
              })
              .where(eq(user.id, expiredUser.id));

            continue;
          }
        } catch (stripeError) {
          console.error(
            `Error fetching Stripe subscription for ${expiredUser.email}:`,
            stripeError
          );
          // Don't downgrade if we can't verify with Stripe
          errorCount++;
          continue;
        }
      }

      // Downgrade to free plan
      await db
        .update(user)
        .set({
          plan: "free",
          planStatus: "expired",
          stripeSubscriptionId: null,
          stripePriceId: null,
          updatedAt: new Date(),
        })
        .where(eq(user.id, expiredUser.id));

      console.log(
        `Downgraded ${expiredUser.email} from ${expiredUser.plan} to free (expired: ${expiredUser.stripeCurrentPeriodEnd})`
      );
      expiredCount++;
    } catch (error) {
      console.error(`Error processing user ${expiredUser.email}:`, error);
      errorCount++;
    }
  }

  console.log(
    `Expired subscriptions check complete: ${expiredUsers.length} checked, ${expiredCount} downgraded, ${errorCount} errors`
  );

  return {
    checked: expiredUsers.length,
    expired: expiredCount,
    errors: errorCount,
  };
}
