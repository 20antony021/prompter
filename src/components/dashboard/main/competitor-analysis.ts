"use server";

import { db } from "@/db";
import { prompts, modelResults, mentions } from "@/db/schema";
import { eq, and, gte, desc, count } from "drizzle-orm";
import { getUser } from "@/auth/server";
import type { SearchResult } from "@/lib/llm";
import { cleanUrl, getDaysAgo } from "@/lib/utils";

// Types for competitor analysis
export interface CompetitorMention {
  name: string;
  url: string;
  mentions: number;
  sentiment: number;
  models: string[];
  avgPosition: number;
  totalSnippetLength: number;
}

export interface CompetitiveIntelligence {
  topCompetitors: CompetitorMention[];
  marketShare: number;
  competitorGap: number;
  yourPosition: number;
  totalCompetitors: number;
}

export interface CompetitorAlert {
  type: "warning" | "success" | "info";
  message: string;
  time: string;
  competitor?: string;
  change?: number;
}

// Helper function to extract brand name from domain or title
function extractBrandName(result: SearchResult): string {
  // Try to get brand name from title first
  let brandName = result.title.toLowerCase().trim();

  // Clean up common prefixes/suffixes
  brandName = brandName
    .replace(/^(the|a|an)\s+/i, "")
    .replace(/\s+(inc|corp|llc|ltd|company|co)\.?$/i, "");

  // If title seems generic or too long, use domain
  if (
    brandName.length < 2 ||
    brandName.includes("best") ||
    brandName.includes("top")
  ) {
    const domain = cleanUrl(result.url);
    brandName = domain.split(".")[0];
  }

  return brandName.charAt(0).toUpperCase() + brandName.slice(1);
}

// Function to calculate sentiment from snippet text
function calculateSentiment(snippet: string): number {
  const positiveWords = [
    "best",
    "top",
    "leading",
    "excellent",
    "great",
    "outstanding",
    "innovative",
    "reliable",
    "trusted",
    "superior",
  ];
  const negativeWords = [
    "worst",
    "bad",
    "poor",
    "terrible",
    "awful",
    "disappointing",
    "unreliable",
    "inferior",
  ];

  const text = snippet.toLowerCase();
  let score = 50; // Neutral baseline

  positiveWords.forEach((word) => {
    if (text.includes(word)) score += 5;
  });

  negativeWords.forEach((word) => {
    if (text.includes(word)) score -= 5;
  });

  return Math.max(0, Math.min(100, score));
}

// Main function to extract competitors from AI results
export async function extractCompetitorsFromResults(
  topicId: string
): Promise<CompetitiveIntelligence> {
  const user = await getUser();
  if (!user) throw new Error("User not found");

  try {
    // Get all model results for the topic
    const results = await db
      .select({
        model: modelResults.model,
        results: modelResults.results,
        createdAt: modelResults.createdAt,
      })
      .from(modelResults)
      .innerJoin(prompts, eq(modelResults.promptId, prompts.id))
      .where(
        and(
          eq(prompts.userId, user.id),
          eq(prompts.topicId, topicId),
          eq(modelResults.status, "completed")
        )
      )
      .orderBy(desc(modelResults.createdAt));

    if (results.length === 0) {
      return {
        topCompetitors: [],
        marketShare: 100,
        competitorGap: 0,
        yourPosition: 1,
        totalCompetitors: 0,
      };
    }

    // Extract competitors from all AI results
    const competitorMap = new Map<
      string,
      {
        name: string;
        url: string;
        mentions: number;
        sentimentScores: number[];
        models: Set<string>;
        positions: number[];
        snippetLengths: number[];
      }
    >();

    // Get your brand mentions for comparison
    const yourMentions = await db
      .select({ count: count() })
      .from(mentions)
      .where(
        and(
          eq(mentions.topicId, topicId),
          gte(mentions.createdAt, getDaysAgo(30))
        )
      );

    const yourBrandMentions = yourMentions[0]?.count || 0;

    // Process each AI result
    results.forEach(({ model, results: searchResults }) => {
      if (!Array.isArray(searchResults)) return;

      searchResults.forEach((result: SearchResult, index: number) => {
        const brandName = extractBrandName(result);
        const domain = cleanUrl(result.url);
        const key = domain; // Use domain as unique identifier

        if (!competitorMap.has(key)) {
          competitorMap.set(key, {
            name: brandName,
            url: result.url,
            mentions: 0,
            sentimentScores: [],
            models: new Set(),
            positions: [],
            snippetLengths: [],
          });
        }

        const competitor = competitorMap.get(key)!;
        competitor.mentions += 1;
        competitor.sentimentScores.push(calculateSentiment(result.snippet));
        competitor.models.add(model);
        competitor.positions.push(index + 1); // 1-indexed position
        competitor.snippetLengths.push(result.snippet.length);
      });
    });

    // Convert to final format and calculate metrics
    const competitors = Array.from(competitorMap.values())
      .map((competitor) => ({
        name: competitor.name,
        url: competitor.url,
        mentions: competitor.mentions,
        sentiment:
          competitor.sentimentScores.length > 0
            ? Math.round(
                competitor.sentimentScores.reduce((a, b) => a + b, 0) /
                  competitor.sentimentScores.length
              )
            : 50,
        models: Array.from(competitor.models),
        avgPosition:
          competitor.positions.length > 0
            ? Math.round(
                competitor.positions.reduce((a, b) => a + b, 0) /
                  competitor.positions.length
              )
            : 0,
        totalSnippetLength: competitor.snippetLengths.reduce(
          (a, b) => a + b,
          0
        ),
      }))
      .sort((a, b) => b.mentions - a.mentions) // Sort by mention count
      .slice(0, 10); // Top 10 competitors

    // Calculate competitive metrics
    const totalCompetitorMentions = competitors.reduce(
      (sum, comp) => sum + comp.mentions,
      0
    );
    const marketShare =
      totalCompetitorMentions > 0
        ? (yourBrandMentions / (yourBrandMentions + totalCompetitorMentions)) *
          100
        : 100;

    const topCompetitor = competitors[0];
    const competitorGap = topCompetitor
      ? ((topCompetitor.mentions - yourBrandMentions) /
          Math.max(yourBrandMentions, 1)) *
        100
      : 0;

    // Calculate your position among all brands
    const allBrands = [{ mentions: yourBrandMentions }, ...competitors].sort(
      (a, b) => b.mentions - a.mentions
    );
    const yourPosition =
      allBrands.findIndex((brand) => brand.mentions === yourBrandMentions) + 1;

    return {
      topCompetitors: competitors.slice(0, 5), // Return top 5 for display
      marketShare: Math.round(marketShare),
      competitorGap: Math.round(competitorGap),
      yourPosition,
      totalCompetitors: competitors.length,
    };
  } catch (error) {
    console.error("Failed to extract competitors:", error);
    return {
      topCompetitors: [],
      marketShare: 100,
      competitorGap: 0,
      yourPosition: 1,
      totalCompetitors: 0,
    };
  }
}

// Function to generate real-time competitive alerts
export async function generateCompetitiveAlerts(
  topicId?: string
): Promise<CompetitorAlert[]> {
  const user = await getUser();
  if (!user) return [];

  const alerts: CompetitorAlert[] = [];

  try {
    // Get current competitive intelligence
    const currentData = await extractCompetitorsFromResults(topicId || "");

    // TODO: Add historical comparison for trend analysis
    // This would compare current vs previous period competitors

    // Analyze competitive changes
    if (currentData.marketShare < 30) {
      alerts.push({
        type: "warning",
        message: `Market share below 30% (${currentData.marketShare}%)`,
        time: "Current",
      });
    }

    if (currentData.competitorGap > 50) {
      const topCompetitor = currentData.topCompetitors[0];
      alerts.push({
        type: "warning",
        message: `${topCompetitor?.name || "Top competitor"} has ${Math.abs(
          currentData.competitorGap
        )}% more mentions`,
        time: "Current",
        competitor: topCompetitor?.name,
        change: currentData.competitorGap,
      });
    }

    if (currentData.yourPosition === 1) {
      alerts.push({
        type: "success",
        message: "Leading in AI search mentions for this topic",
        time: "Current",
      });
    }

    // Check for new competitors
    if (currentData.totalCompetitors > 0) {
      alerts.push({
        type: "info",
        message: `Tracking ${currentData.totalCompetitors} competitors in AI search results`,
        time: "Current",
      });
    }
  } catch (error) {
    console.error("Failed to generate competitive alerts:", error);
  }

  return alerts;
}
