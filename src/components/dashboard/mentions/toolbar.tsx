"use client";

import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, RotateCcw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Status } from "@/types/prompt";

function ProcessMentionsButton({ topicId }: { topicId?: string }) {
  const [currentStatus, setCurrentStatus] = useState<Status>("pending");

  const handleProcess = async () => {
    try {
      setCurrentStatus("processing");

      const response = await fetch("/api/analyze-mentions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topicId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error ?? "Failed to process mentions");
      }

      toast.success("Mentions refresh started, this may take a few minutes");
      setCurrentStatus("completed");
    } catch (error) {
      console.error("Failed to process mentions:", error);
      toast.error("Failed to process mentions");
      setCurrentStatus("failed");
    }
  };

  if (currentStatus === "processing") {
    return (
      <Button
        aria-label="Processing"
        variant="outline"
        size="sm"
        disabled
        className="flex-1 sm:flex-none h-10 px-4"
      >
        <Loader2 className="h-4 w-4 animate-spin" /> Processing...
      </Button>
    );
  }

  if (currentStatus === "failed") {
    return (
      <Button
        aria-label="Retry"
        variant="outline"
        size="sm"
        onClick={handleProcess}
        className="flex-1 sm:flex-none border-red-200 text-red-700 hover:bg-red-50 hover:border-red-300 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950/50 h-10 px-4"
      >
        <RotateCcw className="h-4 w-4" /> Retry
      </Button>
    );
  }

  return (
    <Button
      aria-label="Process mentions"
      size="sm"
      onClick={handleProcess}
      className="flex-1 sm:flex-none bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm h-10 px-4"
    >
      <RefreshCw className="h-4 w-4" /> Process Mentions
    </Button>
  );
}

export function MentionsToolbar({ topicId }: { topicId?: string }) {
  return (
    <div className="flex items-center gap-2 justify-end">
      <ProcessMentionsButton topicId={topicId} />
    </div>
  );
}
