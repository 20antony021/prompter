"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Check, Tag, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import type { TopicSuggestion } from "@/types/topic";
import { LoadingButton } from "@/components/loading-button";
import { topicsApi } from "@/lib/api";
import { useAuth } from "@clerk/nextjs";
import { createTopicFromSuggestion } from "./actions";

interface TopicSuggestionsDialogProps {
  children: React.ReactNode;
}

function TopicSuggestionsListSkeleton() {
  return (
    <div className="space-y-3 mr-3">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="flex items-start gap-3 p-4 rounded-lg border bg-card"
        >
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-4 w-16 rounded-full" />
            </div>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
          <div className="flex gap-1 shrink-0">
            <Skeleton className="h-9 w-9 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  );
}

const fallbackSuggestions: TopicSuggestion[] = [
  {
    id: "fallback_1",
    name: "Shopify",
    description:
      "A leading e‑commerce platform powering millions of merchants worldwide. Strong app ecosystem, robust SEO tooling, and educational content make it a benchmark for product‑led growth and merchant acquisition strategies.",
    category: "E-commerce",
  },
  {
    id: "fallback_2",
    name: "Tesla",
    description:
      "Pioneer of electric vehicles and energy solutions. Known for direct‑to‑consumer sales, bold brand storytelling, and viral product launches that set trends in automotive marketing and community engagement.",
    category: "Automotive",
  },
  {
    id: "fallback_3",
    name: "Notion",
    description:
      "All‑in‑one workspace with viral community adoption. Excels at SEO through templates, internationalization, and creator partnerships that drive organic discovery and retention in productivity software.",
    category: "SaaS",
  },
  {
    id: "fallback_4",
    name: "Netflix",
    description:
      "Global streaming leader that popularized binge watching. Its data‑driven personalization, original content branding, and subscription lifecycle tactics offer rich lessons for growth and retention marketing.",
    category: "Streaming Entertainment",
  },
  {
    id: "fallback_5",
    name: "Asana",
    description:
      "Project management platform for teams. A model for B2B SEO at scale, feature‑led onboarding, and multi‑persona messaging across SMB and enterprise segments in a competitive SaaS category.",
    category: "Project Management Software",
  },
  {
    id: "fallback_6",
    name: "Salesforce",
    description:
      "Dominant CRM vendor with a vast ecosystem. Demonstrates enterprise content strategy, multi‑product cross‑sell motions, and event‑driven brand building around Dreamforce and industry cloud offerings.",
    category: "CRM Software",
  },
  {
    id: "fallback_7",
    name: "Airbnb",
    description:
      "Marketplace for stays and experiences. Blends community storytelling with scalable SEO on location pages and trust signals, shaping how peer‑to‑peer platforms drive both supply and demand.",
    category: "Travel",
  },
  {
    id: "fallback_8",
    name: "Google",
    description:
      "Search and AI company defining consumer discovery. Offers insights into SERP feature evolution, product surfaces like Maps and YouTube, and platform effects on brand visibility and performance.",
    category: "Technology",
  },
  {
    id: "fallback_9",
    name: "Amazon",
    description:
      "Commerce and cloud giant. Reveals marketplace SEO dynamics, logistics‑driven conversion strategy, and Prime‑centric retention that influence how brands compete for high‑intent traffic.",
    category: "E-commerce",
  },
  {
    id: "fallback_10",
    name: "Microsoft",
    description:
      "Diversified technology leader across cloud, productivity, and AI. Showcases multi‑brand navigation, enterprise developer marketing, and integration plays from Windows to Azure and Copilot.",
    category: "Technology",
  },
  {
    id: "fallback_11",
    name: "NVIDIA",
    description:
      "Semiconductor and AI infrastructure powerhouse. Illustrates category creation around GPUs, platform ecosystems with CUDA, and thought leadership in AI research driving enterprise demand.",
    category: "Semiconductors",
  },
  {
    id: "fallback_12",
    name: "TikTok",
    description:
      "Short‑video platform shaping culture and commerce. Provides a lens on creator‑led growth, algorithmic discovery, and social shopping features that brands leverage for awareness and conversion.",
    category: "Social Media",
  },
];

export function TopicSuggestionsDialog({
  children,
}: TopicSuggestionsDialogProps) {
  const [loading, setLoading] = useState(true);
  const [suggestions, setSuggestions] = useState<TopicSuggestion[]>(fallbackSuggestions);
  const [open, setOpen] = useState(false);
  const { getToken } = useAuth();

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    async function run() {
      try {
        setLoading(true);
        const token = await getToken().catch(() => null);
        const res = await topicsApi.getSuggestions(undefined, token || undefined);
        const data = res.data as TopicSuggestion[];
        if (!cancelled && Array.isArray(data) && data.length) {
          setSuggestions(data);
        }
      } catch (e) {
        console.warn("Using fallback topic suggestions due to error:", e);
        // Keep fallbackSuggestions
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [open]);


  return (
    <Dialog open={open} onOpenChange={(v) => {
      setOpen(v);
      if (v) setLoading(true);
    }}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>AI-Generated Topic Suggestions</DialogTitle>
          <DialogDescription>
            Here are some AI-generated suggestions for interesting brands and
            companies to analyze.
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-[500px] overflow-y-auto">
          {loading ? (
            <div className="space-y-3 mr-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Generating AI suggestions… This can take a few seconds.</span>
              </div>
              <div className="h-1 w-full bg-secondary/40 rounded overflow-hidden">
                <div className="h-full w-1/3 bg-primary/60 animate-pulse rounded" />
              </div>
              <TopicSuggestionsListSkeleton />
            </div>
          ) : (
            <div className="space-y-3 mr-3">
              {suggestions.map((suggestion) => (
                <div
                  key={suggestion.id}
                  className="flex items-start gap-3 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-sm font-semibold">{suggestion.name}</h4>
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-secondary text-secondary-foreground">
                        <Tag className="h-3 w-3" />
                        {suggestion.category}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {suggestion.description}
                    </p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <form action={createTopicFromSuggestion}>
                      <input type="hidden" name="name" value={suggestion.name} />
                      <input type="hidden" name="description" value={suggestion.description} />
                      <input
                        type="hidden"
                        name="logo"
                        value={suggestion.name.toLowerCase().replace(/\s+/g, "") + ".com"}
                      />
                      <LoadingButton aria-label="Add topic" size="icon" variant="outline">
                        <Check className="h-4 w-4" />
                        <span className="sr-only">Accept topic suggestion</span>
                      </LoadingButton>
                    </form>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
