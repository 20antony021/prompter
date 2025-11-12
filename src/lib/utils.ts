import { LLMResult } from "@/types/prompt";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const cleanUrl = (url: string) => {
  if (!url) return "";

  const urlWithProtocol = url.startsWith("http") ? url : `https://${url}`;
  const urlObj = new URL(urlWithProtocol);
  return urlObj.hostname.toLowerCase().replace(/^www\./, "");
};

// Date utility functions to reduce duplication
export const getDaysAgo = (days: number): Date => {
  const now = new Date();
  return new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
};

export const getDateRanges = () => {
  return {
    now: new Date(),
    thirtyDaysAgo: getDaysAgo(30),
    sixtyDaysAgo: getDaysAgo(60),
  };
};

export const getVisibilityScore = (results: LLMResult[], brandName: string) => {
  const completedResults = results.filter(
    (result) => result.status === "completed" && result.results.length > 0
  );

  if (completedResults.length === 0) return 0;

  const scores = completedResults.map((llmResult) => {
    const brandNameLower = brandName.toLowerCase();

    const position = llmResult.results.findIndex(
      (searchResult) =>
        searchResult.title.toLowerCase() === brandNameLower ||
        searchResult.title.toLowerCase().includes(brandNameLower) ||
        brandNameLower.includes(searchResult.title.toLowerCase())
    );

    if (position === -1) return 0;

    const totalResults = llmResult.results.length;
    const score = ((totalResults - position) / totalResults) * 100;

    return score;
  });

  const averageScore =
    scores.reduce((sum, score) => sum + score, 0) / scores.length;

  return Math.round(averageScore * 100) / 100;
};

export const getVisibilityScoreColor = (score: number) => {
  if (score > 90) return "text-green-600";
  if (score > 70) return "text-yellow-600";
  if (score > 50) return "text-orange-600";
  if (score > 30) return "text-red-600";
  return "text-gray-500";
};
