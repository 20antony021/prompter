"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Plus, Lightbulb } from "lucide-react";
import { CreateTopicDialog } from "./create-dialog";
import { TopicSuggestionsDialog } from "./suggestions-dialog";

interface TopicsToolbarProps {
  search?: string;
}

export function TopicsToolbar({ search = "" }: TopicsToolbarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const [value, setValue] = useState(search);

  useEffect(() => {
    setValue(search);
  }, [search]);

  const debouncedValue = useDebounce(value, 300);

  useEffect(() => {
    const params = new URLSearchParams(sp?.toString());
    if (debouncedValue && debouncedValue.trim().length > 0) {
      params.set("q", debouncedValue.trim());
    } else {
      params.delete("q");
    }
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname);
  }, [debouncedValue, pathname, router, sp]);

  return (
    <div className="flex items-center justify-between flex-col gap-2 sm:flex-row">
      <div className="relative w-full sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Search by topic name"
          className="pl-9"
        />
      </div>
      <div className="flex items-center gap-2 w-full sm:w-auto">
        <CreateTopicDialog>
          <Button variant="default" size="sm" className="gap-2 flex-1">
            <Plus className="h-4 w-4" />
            Create Topic
          </Button>
        </CreateTopicDialog>
        <TopicSuggestionsDialog>
          <Button variant="outline" size="sm" className="gap-2 flex-1">
            <Lightbulb className="h-4 w-4" />
            Suggestions
          </Button>
        </TopicSuggestionsDialog>
      </div>
    </div>
  );
}

function useDebounce<T>(value: T, delay: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return useMemo(() => debounced, [debounced]);
}
