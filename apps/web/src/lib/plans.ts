/**
 * Pricing plan configurations for display and reference.
 * These should match the backend PLAN_QUOTAS in apps/api/app/config.py
 */

export interface PlanFeatures {
  price: number;
  brands: number;
  prompts: number;
  scans: number;
  pages: number;
  seats: number | "Unlimited";
  retention: number;
  support: string;
}

export const PLANS: Record<string, PlanFeatures> = {
  starter: {
    price: 89,
    brands: 1,
    prompts: 30,
    scans: 1000,
    pages: 3,
    seats: 3,
    retention: 30,
    support: "Email",
  },
  pro: {
    price: 289,
    brands: 3,
    prompts: 150,
    scans: 5000,
    pages: 10,
    seats: 10,
    retention: 180,
    support: "Email + Slack",
  },
  business: {
    price: 489,
    brands: 10,
    prompts: 500,
    scans: 15000,
    pages: 25,
    seats: "Unlimited",
    retention: 365,
    support: "Priority + 99.9% SLA",
  },
};

export interface UsageMetric {
  used: number;
  limit: number | null;
  warn: boolean;
}

export interface UsageData {
  scans: UsageMetric;
  prompts: UsageMetric;
  ai_pages: UsageMetric;
}

/**
 * Check if a usage metric is at or over the limit.
 */
export function isAtLimit(metric: UsageMetric): boolean {
  if (metric.limit === null) return false; // Unlimited
  return metric.used >= metric.limit;
}

/**
 * Check if a usage metric is approaching the limit (>= 80%).
 */
export function isApproachingLimit(metric: UsageMetric): boolean {
  return metric.warn;
}

/**
 * Format usage display string (e.g., "450 / 1,000" or "25 / Unlimited").
 */
export function formatUsage(metric: UsageMetric): string {
  const used = metric.used.toLocaleString();
  const limit = metric.limit === null ? "Unlimited" : metric.limit.toLocaleString();
  return `${used} / ${limit}`;
}

/**
 * Calculate percentage used (0-100, or null if unlimited).
 */
export function calculatePercentage(metric: UsageMetric): number | null {
  if (metric.limit === null) return null;
  if (metric.limit === 0) return 0;
  return Math.min(100, Math.round((metric.used / metric.limit) * 100));
}

