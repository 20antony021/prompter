"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Plus, Lightbulb } from "lucide-react";
import { CreateTopicDialog } from "./create-dialog";
import { TopicSuggestionsDialog } from "./suggestions-dialog";
import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

export function TopicsToolbar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();
  const searchQuery = searchParams.get("q") || "";

  const handleSearch = (value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set("q", value);
    } else {
      params.delete("q");
    }
    startTransition(() => {
      router.push(`/dashboard/topics?${params.toString()}`);
    });
  };

  return (
    <div className="flex items-center justify-between flex-col gap-2 sm:flex-row">
      <div className="relative w-full sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search by topic name"
          defaultValue={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          className="pl-9 h-10 border-border bg-background/50 backdrop-blur-sm transition-all focus-visible:bg-background"
        />
      </div>
      <div className="flex items-center gap-2 w-full sm:w-auto">
        <CreateTopicDialog>
          <Button
            size="sm"
            className="gap-2 flex-1 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm h-10 px-4"
          >
            <Plus className="h-4 w-4" />
            Create Topic
          </Button>
        </CreateTopicDialog>
        <TopicSuggestionsDialog>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 flex-1 border-indigo-200 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-300 dark:border-indigo-800 dark:text-indigo-400 dark:hover:bg-indigo-950/50 h-10 px-4"
          >
            <Lightbulb className="h-4 w-4" />
            Suggestions
          </Button>
        </TopicSuggestionsDialog>
      </div>
    </div>
  );
}
