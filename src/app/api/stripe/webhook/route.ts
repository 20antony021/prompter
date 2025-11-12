import { NextRequest, NextResponse } from "next/server";
import { PlanType, stripe, type Stripe } from "@/lib/stripe/server";
import { db } from "@/db";
import { user } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json(
      { error: "No Stripe signature found" },
      { status: 400 }
    );
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (error) {
    console.error("Webhook signature verification failed:", error);
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  try {
    console.log(`Processing webhook event: ${event.type}`);

    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object;
        await handleCheckoutCompleted(session);
        break;
      }

      case "customer.subscription.created": {
        const subscription = event.data.object;
        await handleSubscriptionCreated(subscription);
        break;
      }

      case "customer.subscription.updated": {
        const subscription = event.data.object;
        await handleSubscriptionUpdated(subscription);
        break;
      }

      case "customer.subscription.deleted": {
        const subscription = event.data.object;
        await handleSubscriptionDeleted(subscription);
        break;
      }

      case "invoice.payment_succeeded": {
        const invoice = event.data.object;
        await handlePaymentSucceeded(invoice);
        break;
      }

      case "invoice.payment_failed": {
        const invoice = event.data.object;
        await handlePaymentFailed(invoice);
        break;
      }

      case "customer.subscription.trial_will_end": {
        const subscription = event.data.object;
        await handleTrialWillEnd(subscription);
        break;
      }

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error("Webhook handler error:", error);
    return NextResponse.json(
      { error: "Webhook handler failed" },
      { status: 500 }
    );
  }
}

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  if (!session.customer || !session.subscription) {
    console.error("Missing customer or subscription in checkout session");
    return;
  }

  const customerId = session.customer;
  const subscriptionId = session.subscription;

  if (typeof customerId !== "string" || typeof subscriptionId !== "string") {
    console.error("Invalid customer or subscription in checkout session");
    return;
  }

  let subscription: Stripe.Subscription;

  try {
    subscription = await stripe.subscriptions.retrieve(subscriptionId);
  } catch (error) {
    console.error("Error retrieving subscription:", error);
    return;
  }

  const priceId = subscription.items.data[0]?.price.id;

  if (!priceId) {
    console.error("No price ID found in subscription");
    return;
  }

  let planType: PlanType = "free";
  if (priceId === process.env.STRIPE_BASIC_PRICE_ID) {
    planType = "basic";
  } else if (priceId === process.env.STRIPE_PRO_PRICE_ID) {
    planType = "pro";
  } else if (priceId === process.env.STRIPE_ENTERPRISE_PRICE_ID) {
    planType = "enterprise";
  }

  // Use subscription.current_period_end, not items.data[0].current_period_end
  // Note: Stripe types may not include all properties; using type assertion
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const currentPeriodEnd = (subscription as any).current_period_end as number | undefined;

  await db
    .update(user)
    .set({
      stripeCustomerId: customerId,
      stripeSubscriptionId: subscriptionId,
      stripePriceId: priceId,
      stripeCurrentPeriodEnd: currentPeriodEnd
        ? new Date(currentPeriodEnd * 1000)
        : null,
      plan: planType,
      planStatus: subscription.status === "active" ? "active" : subscription.status,
      updatedAt: new Date(),
    })
    .where(eq(user.stripeCustomerId, customerId));

  console.log(
    `User upgraded to ${planType} plan (subscription: ${subscriptionId}, status: ${subscription.status})`
  );
}

async function handleSubscriptionCreated(subscription: Stripe.Subscription) {
  const customerId = subscription.customer;

  if (typeof customerId !== "string") {
    console.error("Invalid customer in subscription");
    return;
  }

  const priceId = subscription.items.data[0]?.price.id;
  if (!priceId) {
    console.error("No price ID found in subscription");
    return;
  }

  let planType: PlanType = "free";
  if (priceId === process.env.STRIPE_BASIC_PRICE_ID) {
    planType = "basic";
  } else if (priceId === process.env.STRIPE_PRO_PRICE_ID) {
    planType = "pro";
  } else if (priceId === process.env.STRIPE_ENTERPRISE_PRICE_ID) {
    planType = "enterprise";
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const currentPeriodEnd = (subscription as any).current_period_end as number | undefined;

  await db
    .update(user)
    .set({
      stripeSubscriptionId: subscription.id,
      stripePriceId: priceId,
      stripeCurrentPeriodEnd: currentPeriodEnd
        ? new Date(currentPeriodEnd * 1000)
        : null,
      plan: planType,
      planStatus: subscription.status,
      updatedAt: new Date(),
    })
    .where(eq(user.stripeCustomerId, customerId));

  console.log(
    `Subscription created for customer ${customerId} (plan: ${planType}, status: ${subscription.status})`
  );
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription) {
  const customerId = subscription.customer;

  if (typeof customerId !== "string") {
    console.error("Invalid customer in subscription");
    return;
  }

  const priceId = subscription.items.data[0]?.price.id;
  if (!priceId) {
    console.error("No price ID found in subscription");
    return;
  }

  let planType: PlanType = "free";
  if (priceId === process.env.STRIPE_BASIC_PRICE_ID) {
    planType = "basic";
  } else if (priceId === process.env.STRIPE_PRO_PRICE_ID) {
    planType = "pro";
  } else if (priceId === process.env.STRIPE_ENTERPRISE_PRICE_ID) {
    planType = "enterprise";
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const currentPeriodEnd = (subscription as any).current_period_end as number | undefined;

  // Handle subscription status changes
  let newPlanStatus = subscription.status;
  let newPlan = planType;

  // If subscription is canceled/expired, downgrade to free
  if (
    subscription.status === "canceled" ||
    subscription.status === "unpaid" ||
    subscription.status === "incomplete_expired"
  ) {
    newPlan = "free";
    newPlanStatus = "canceled";
  }

  await db
    .update(user)
    .set({
      stripeSubscriptionId: subscription.id,
      stripePriceId: priceId,
      stripeCurrentPeriodEnd: currentPeriodEnd
        ? new Date(currentPeriodEnd * 1000)
        : null,
      plan: newPlan,
      planStatus: newPlanStatus,
      updatedAt: new Date(),
    })
    .where(eq(user.stripeCustomerId, customerId));

  console.log(
    `Subscription updated for customer ${customerId} (plan: ${newPlan}, status: ${newPlanStatus})`
  );
}

async function handleSubscriptionDeleted(subscription: Stripe.Subscription) {
  const customerId = subscription.customer;

  if (typeof customerId !== "string") {
    console.error("Invalid customer in subscription");
    return;
  }

  try {
    await db
      .update(user)
      .set({
        stripeSubscriptionId: null,
        stripePriceId: null,
        stripeCurrentPeriodEnd: null,
        plan: "free",
        planStatus: "canceled",
        updatedAt: new Date(),
      })
      .where(eq(user.stripeCustomerId, customerId));

    console.log(`Subscription canceled for customer ${customerId}`);
  } catch (error) {
    console.error("Error canceling subscription:", error);
    return;
  }
}

async function handlePaymentSucceeded(invoice: Stripe.Invoice) {
  const customerId = invoice.customer;

  if (typeof customerId !== "string") {
    console.error("Invalid customer in invoice");
    return;
  }

  // Fetch the subscription to get the latest period end
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const invoiceSubscription = (invoice as any).subscription;
  if (invoiceSubscription && typeof invoiceSubscription === "string") {
    try {
      const subscription = await stripe.subscriptions.retrieve(
        invoiceSubscription
      );

      const priceId = subscription.items.data[0]?.price.id;
      if (!priceId) return;

      let planType: PlanType = "free";
      if (priceId === process.env.STRIPE_BASIC_PRICE_ID) {
        planType = "basic";
      } else if (priceId === process.env.STRIPE_PRO_PRICE_ID) {
        planType = "pro";
      } else if (priceId === process.env.STRIPE_ENTERPRISE_PRICE_ID) {
        planType = "enterprise";
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const currentPeriodEnd = (subscription as any).current_period_end as number | undefined;

      await db
        .update(user)
        .set({
          stripeCurrentPeriodEnd: currentPeriodEnd
            ? new Date(currentPeriodEnd * 1000)
            : null,
          plan: planType,
          planStatus: "active",
          updatedAt: new Date(),
        })
        .where(eq(user.stripeCustomerId, customerId));

      console.log(
        `Payment succeeded for customer ${customerId}, subscription renewed until ${currentPeriodEnd ? new Date(currentPeriodEnd * 1000).toISOString() : 'unknown'}`
      );
    } catch (error) {
      console.error("Error processing payment success:", error);
    }
  }
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  const customerId = invoice.customer;

  if (typeof customerId !== "string") {
    console.error("Invalid customer in invoice");
    return;
  }

  await db
    .update(user)
    .set({
      planStatus: "past_due",
      updatedAt: new Date(),
    })
    .where(eq(user.stripeCustomerId, customerId));

  console.log(`Payment failed for customer ${customerId}, marked as past_due`);
}

async function handleTrialWillEnd(subscription: Stripe.Subscription) {
  const customerId = subscription.customer;

  if (typeof customerId !== "string") {
    console.error("Invalid customer in subscription");
    return;
  }

  console.log(
    `Trial will end soon for customer ${customerId} (subscription: ${subscription.id})`
  );
  // You can add email notification logic here
}
