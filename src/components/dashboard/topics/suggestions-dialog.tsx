"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Check, Loader2, Tag, X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  generateTopicSuggestions,
  type TopicSuggestion,
} from "@/lib/suggestions";
import { createTopicFromUrlLegacy } from "./actions";
import { cn } from "@/lib/utils";

interface TopicSuggestionsDialogProps {
  children: React.ReactNode;
}

const fallbackSuggestions: TopicSuggestion[] = [
  {
    id: "fallback_1",
    name: "Shopify",
    description:
      "Leading e-commerce platform with strong SEO presence and diverse merchant ecosystem",
    category: "E-commerce",
  },
  {
    id: "fallback_2",
    name: "Tesla",
    description:
      "Innovative automotive brand with unique marketing approach and strong brand presence",
    category: "Automotive",
  },
  {
    id: "fallback_3",
    name: "Notion",
    description:
      "Fast-growing productivity SaaS with community-driven growth and content marketing",
    category: "SaaS",
  },
];

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
            <Skeleton className="h-9 w-9 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  );
}

function TopicSuggestionsList() {
  const [suggestions, setSuggestions] = useState<TopicSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successes, setSuccesses] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function fetchSuggestions() {
      try {
        const data = await generateTopicSuggestions();
        setSuggestions(data);
      } catch (error) {
        console.error("Failed to generate topic suggestions:", error);
        setSuggestions(fallbackSuggestions);
      } finally {
        setLoading(false);
      }
    }
    fetchSuggestions();
  }, []);

  const handleAccept = async (suggestion: TopicSuggestion) => {
    setLoadingStates((prev) => ({ ...prev, [suggestion.id]: true }));
    setErrors((prev) => ({ ...prev, [suggestion.id]: "" }));

    try {
      const result = await createTopicFromUrlLegacy({
        url: suggestion.name.toLowerCase().replace(/\s+/g, "") + ".com",
      });

      if (result.success) {
        setSuccesses((prev) => ({ ...prev, [suggestion.id]: true }));
        // Auto-clear success state after 2s
        setTimeout(() => {
          setSuccesses((prev) => ({ ...prev, [suggestion.id]: false }));
        }, 2000);
      } else {
        setErrors((prev) => ({ ...prev, [suggestion.id]: result.error || "Failed to create topic" }));
      }
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        [suggestion.id]: error instanceof Error ? error.message : "Unknown error occurred"
      }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, [suggestion.id]: false }));
    }
  };

  const clearError = (suggestionId: string) => {
    setErrors((prev) => ({ ...prev, [suggestionId]: "" }));
  };

  if (loading) {
    return <TopicSuggestionsListSkeleton />;
  }

  return (
    <div className="space-y-3 mr-3">
      {suggestions.map((suggestion) => (
        <div key={suggestion.id} className="space-y-2">
          <div
            className={cn(
              "flex items-start gap-3 p-4 rounded-lg border bg-card transition-all shadow-sm",
              successes[suggestion.id]
                ? "bg-green-50 border-green-200 dark:bg-green-950/20 dark:border-green-800"
                : errors[suggestion.id]
                ? "bg-destructive/5 border-destructive/20"
                : "hover:bg-muted/50"
            )}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="text-sm font-semibold">{suggestion.name}</h4>
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-400 font-medium">
                  <Tag className="h-3 w-3" />
                  {suggestion.category}
                </span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {suggestion.description}
              </p>
            </div>
            <div className="flex gap-1 shrink-0">
              <Button
                type="button"
                size="icon"
                variant="outline"
                title="Add this topic"
                disabled={loadingStates[suggestion.id] || successes[suggestion.id]}
                onClick={() => handleAccept(suggestion)}
                className={cn(
                  "transition-all",
                  successes[suggestion.id]
                    ? "bg-green-500 text-white border-green-500 hover:bg-green-600 hover:border-green-600"
                    : "hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 dark:hover:bg-indigo-950/50 dark:hover:border-indigo-800 dark:hover:text-indigo-400"
                )}
              >
                {loadingStates[suggestion.id] ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : successes[suggestion.id] ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Check className="h-4 w-4" />
                )}
                <span className="sr-only">Accept topic suggestion</span>
              </Button>
            </div>
          </div>

          {/* Error Message */}
          {errors[suggestion.id] && (
            <div
              className={cn(
                "flex items-start gap-3 p-4 border rounded-lg animate-in slide-in-from-top-2 fade-in duration-300",
                "bg-destructive/5 border-destructive/20 text-destructive"
              )}
            >
              <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium">Error</p>
                <p className="text-sm opacity-80">{errors[suggestion.id]}</p>
              </div>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                onClick={() => clearError(suggestion.id)}
                className="h-6 w-6 shrink-0 hover:bg-destructive/10"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Dismiss error</span>
              </Button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function TopicSuggestionsDialog({
  children,
}: TopicSuggestionsDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-2xl border-border shadow-lg">
        <DialogHeader className="space-y-3">
          <DialogTitle className="text-xl font-semibold">
            AI-Generated Topic Suggestions
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Here are some AI-generated suggestions for interesting brands and
            companies to analyze.
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-[500px] overflow-y-auto">
          <TopicSuggestionsList />
        </div>
      </DialogContent>
    </Dialog>
  );
}
