import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { Webhook } from "svix";
import { db } from "@/db";
import { user as userTable } from "@/db/schema";
import { eq } from "drizzle-orm";

type ClerkWebhookEvent = {
  type: string;
  data: {
    id: string;
    email_addresses?: Array<{
      id: string;
      email_address: string;
    }>;
    primary_email_address_id?: string;
    first_name?: string;
    last_name?: string;
    image_url?: string;
    email_verified?: boolean;
  };
};

/**
 * Verify Svix webhook signature using official Svix SDK
 */
function verifySvixSignature(
  payload: string,
  headersList: Headers,
  secret: string
): boolean {
  try {
    const svixId = headersList.get("svix-id");
    const svixTimestamp = headersList.get("svix-timestamp");
    const svixSignature = headersList.get("svix-signature");

    console.log("🔐 Verifying signature with Svix SDK...");
    console.log("  svix-id:", svixId);
    console.log("  svix-timestamp:", svixTimestamp);
    console.log(
      "  svix-signature:",
      svixSignature
        ? `${svixSignature.substring(0, 50)}...`
        : svixSignature
    );
    console.log("  secret configured:", secret ? "Yes" : "No");

    if (!secret) {
      console.error("❌ CLERK_WEBHOOK_SECRET not configured!");
      return false;
    }

    if (!svixId || !svixTimestamp || !svixSignature) {
      console.warn("❌ Missing required Svix headers");
      return false;
    }

    // Use official Svix SDK for verification
    const wh = new Webhook(secret);

    // Svix SDK expects headers as an object with specific keys
    const headersObject = {
      "svix-id": svixId,
      "svix-timestamp": svixTimestamp,
      "svix-signature": svixSignature,
    };

    // Verify and parse the webhook payload
    wh.verify(payload, headersObject);

    console.log("✅ Signature verified successfully with Svix SDK!");
    return true;
  } catch (error) {
    console.error("❌ Webhook verification failed:", error);
    return false;
  }
}

export async function POST(req: Request) {
  try {
    // Get raw body for signature verification
    const payload = await req.text();
    const headersList = await headers();

    // Verify webhook signature in production
    const webhookSecret = process.env.CLERK_WEBHOOK_SECRET;

    if (webhookSecret) {
      if (!verifySvixSignature(payload, headersList, webhookSecret)) {
        console.error("Webhook signature verification failed");
        return NextResponse.json(
          { error: "Invalid webhook signature" },
          { status: 401 }
        );
      }
      console.log("Webhook signature verified successfully");
    } else {
      console.warn(
        "CLERK_WEBHOOK_SECRET not set - skipping signature verification (DEV MODE ONLY)"
      );
    }

    // Parse the webhook payload
    const event: ClerkWebhookEvent = JSON.parse(payload);
    const eventType = event.type;
    const eventData = event.data;

    console.log(`📨 Received Clerk webhook: ${eventType}`);

    switch (eventType) {
      case "user.created": {
        console.log("Processing user.created event");

        // Extract user information from Clerk
        const userId = eventData.id;
        const emailAddresses = eventData.email_addresses || [];
        let primaryEmail: string | null = null;

        // Find primary email
        for (const email of emailAddresses) {
          if (email.id === eventData.primary_email_address_id) {
            primaryEmail = email.email_address;
            break;
          }
        }

        if (!primaryEmail && emailAddresses.length > 0) {
          primaryEmail = emailAddresses[0].email_address;
        }

        // Get user name
        const firstName = eventData.first_name || "";
        const lastName = eventData.last_name || "";
        const name = `${firstName} ${lastName}`.trim() || "User";

        console.log(
          `Creating user: ${userId}, email: ${primaryEmail}, name: ${name}`
        );

        // Check if user already exists
        const existingUsers = await db
          .select()
          .from(userTable)
          .where(eq(userTable.id, userId))
          .limit(1);

        if (existingUsers.length === 0) {
          // Create new user
          await db.insert(userTable).values({
            id: userId,
            email: primaryEmail || `${userId}@clerk.user`,
            name,
            emailVerified: eventData.email_verified || false,
            image: eventData.image_url,
            plan: "free",
            planStatus: "active",
          });

          console.log(`✅ User created successfully: ${userId}`);
          return NextResponse.json({
            status: "success",
            message: "User created",
            user_id: userId,
          });
        } else {
          console.log(`User already exists: ${userId}`);
          return NextResponse.json({
            status: "success",
            message: "User already exists",
            user_id: userId,
          });
        }
      }

      case "user.updated": {
        console.log("Processing user.updated event");

        const userId = eventData.id;
        const existingUsers = await db
          .select()
          .from(userTable)
          .where(eq(userTable.id, userId))
          .limit(1);

        if (existingUsers.length > 0) {
          const user = existingUsers[0];

          // Extract updated email
          const emailAddresses = eventData.email_addresses || [];
          let updatedEmail = user.email;

          for (const email of emailAddresses) {
            if (email.id === eventData.primary_email_address_id) {
              updatedEmail = email.email_address;
              break;
            }
          }

          // Extract updated name
          const firstName = eventData.first_name || "";
          const lastName = eventData.last_name || "";
          let updatedName = user.name;

          if (firstName || lastName) {
            updatedName = `${firstName} ${lastName}`.trim();
          }

          // Update user information
          await db
            .update(userTable)
            .set({
              email: updatedEmail,
              name: updatedName,
              image: eventData.image_url || user.image,
              emailVerified: eventData.email_verified ?? user.emailVerified,
              updatedAt: new Date(),
            })
            .where(eq(userTable.id, userId));

          console.log(`✅ User updated successfully: ${userId}`);
          return NextResponse.json({
            status: "success",
            message: "User updated",
            user_id: userId,
          });
        } else {
          // User doesn't exist, create it
          console.log(
            `User not found for update, creating new user: ${userId}`
          );

          const emailAddresses = eventData.email_addresses || [];
          let primaryEmail: string | null = null;

          for (const email of emailAddresses) {
            if (email.id === eventData.primary_email_address_id) {
              primaryEmail = email.email_address;
              break;
            }
          }

          if (!primaryEmail && emailAddresses.length > 0) {
            primaryEmail = emailAddresses[0].email_address;
          }

          const firstName = eventData.first_name || "";
          const lastName = eventData.last_name || "";
          const name = `${firstName} ${lastName}`.trim() || "User";

          await db.insert(userTable).values({
            id: userId,
            email: primaryEmail || `${userId}@clerk.user`,
            name,
            emailVerified: eventData.email_verified || false,
            image: eventData.image_url,
            plan: "free",
            planStatus: "active",
          });

          console.log(`✅ User created successfully: ${userId}`);
          return NextResponse.json({
            status: "success",
            message: "User created",
            user_id: userId,
          });
        }
      }

      case "user.deleted": {
        console.log("Processing user.deleted event");

        const userId = eventData.id;
        const existingUsers = await db
          .select()
          .from(userTable)
          .where(eq(userTable.id, userId))
          .limit(1);

        if (existingUsers.length > 0) {
          // Soft delete: you might want to add a 'deleted_at' column
          // For now, we'll just return success
          // Hard delete (not recommended):
          // await db.delete(userTable).where(eq(userTable.id, userId));

          console.log(`✅ User deletion noted: ${userId}`);
          return NextResponse.json({
            status: "success",
            message: "User deletion noted",
            user_id: userId,
          });
        }

        return NextResponse.json({
          status: "success",
          message: "User not found",
          user_id: userId,
        });
      }

      default: {
        console.log(`Event ${eventType} received but not processed`);
        return NextResponse.json({
          status: "success",
          message: `Event ${eventType} received but not processed`,
        });
      }
    }
  } catch (error) {
    console.error("Webhook processing error:", error);
    return NextResponse.json(
      {
        error: "Webhook processing error",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 400 }
    );
  }
}
