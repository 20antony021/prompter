"use client";

import { Button } from "@/components/ui/button";
import { Loader2, RotateCcw, Search } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Status } from "@/types/prompt";
import { toast } from "sonner";

interface ProcessButtonProps {
  promptId: string;
  status: Status;
}

export function ProcessButton({ promptId, status }: ProcessButtonProps) {
  const [currentStatus, setCurrentStatus] = useState(status);
  const router = useRouter();

  useEffect(() => {
    if (currentStatus !== "processing") return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/prompts/${promptId}/status`);
        if (response.ok) {
          const data = await response.json();

          if (data.status !== currentStatus) {
            setCurrentStatus(data.status);
          }

          if (data.status !== "processing") {
            router.refresh();
            clearInterval(pollInterval);
          }

          if (data.status === "failed") {
            toast.error("Failed to process prompt");
          }

          if (data.status === "completed") {
            toast.success("Prompt processed successfully");
          }
        }
      } catch (error) {
        console.error("Failed to poll status:", error);
      }
    }, 4000);

    return () => clearInterval(pollInterval);
  }, [currentStatus, promptId, router]);

  const handleProcess = async () => {
    try {
      setCurrentStatus("processing");

      const response = await fetch("/api/prompts/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ promptId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error ?? "Failed to process prompt");
      }
    } catch (error) {
      console.error("Failed to process prompt:", error);
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
        className="h-8"
      >
        <Loader2 className="h-4 w-4 animate-spin" />
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
        className="h-8 hover:bg-red-50 hover:border-red-300 hover:text-red-700 dark:hover:bg-red-950/50 dark:hover:border-red-800 dark:hover:text-red-400 transition-all"
      >
        <RotateCcw className="h-4 w-4" />
      </Button>
    );
  }

  return (
    <Button
      aria-label="Process prompt"
      variant="outline"
      size="sm"
      onClick={handleProcess}
      className="h-8 hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 dark:hover:bg-indigo-950/50 dark:hover:border-indigo-800 dark:hover:text-indigo-400 transition-all"
    >
      <Search className="h-4 w-4" />
    </Button>
  );
}
