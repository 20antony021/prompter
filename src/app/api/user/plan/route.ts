import { auth } from "@clerk/nextjs/server";
import { db } from "@/db";
import { user as userTable } from "@/db/schema";
import { eq } from "drizzle-orm";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const { getToken, userId: syncUserId } = await auth();
    const token = await getToken();
    console.log("Fetching plan for user:", syncUserId);

    if (!token || !syncUserId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Fetch user data from database
    const users = await db
      .select({
        plan: userTable.plan,
        stripeCustomerId: userTable.stripeCustomerId,
      })
      .from(userTable)
      .where(eq(userTable.id, syncUserId))
      .limit(1);

    const user = users[0];

    return NextResponse.json({
      plan: user?.plan || "free",
      stripeCustomerId: user?.stripeCustomerId || null,
    });
  } catch (error) {
    console.error("Failed to fetch user data:", error);
    return NextResponse.json({
      plan: "free",
      stripeCustomerId: null,
    }, { status: 200 });
  }
}
