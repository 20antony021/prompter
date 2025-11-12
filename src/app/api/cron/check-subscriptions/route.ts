import { NextRequest, NextResponse } from "next/server";
import { checkAllExpiredSubscriptions } from "@/lib/subscription/check-expired";

export const runtime = "nodejs";
export const maxDuration = 300; // 5 minutes

/**
 * Cron job to check for expired subscriptions
 * This runs daily to catch any subscriptions that expired but weren't caught by webhooks
 *
 * Set up in vercel.json:
 * {
 *   "crons": [{
 *     "path": "/api/cron/check-subscriptions",
 *     "schedule": "0 2 * * *"
 *   }]
 * }
 */
export async function GET(request: NextRequest) {
  // Verify this is from Vercel Cron
  const authHeader = request.headers.get("authorization");

  if (process.env.NODE_ENV === "production") {
    // In production, verify the cron secret
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  }

  try {
    console.log("Starting scheduled subscription check...");

    const results = await checkAllExpiredSubscriptions();

    return NextResponse.json({
      success: true,
      timestamp: new Date().toISOString(),
      results,
    });
  } catch (error) {
    console.error("Cron job failed:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
