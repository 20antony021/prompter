"use client";

import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useTransition } from "react";

export function RankingsSearchBox() {
  const router = useRouter();
  const pathname = usePathname();
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
      router.push(`${pathname}?${params.toString()}`);
    });
  };

  return (
    <div className="relative w-full sm:max-w-xs">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        placeholder="Search by prompt name"
        defaultValue={searchQuery}
        onChange={(e) => handleSearch(e.target.value)}
        className="pl-9 h-10 border-border bg-background/50 backdrop-blur-sm transition-all focus-visible:bg-background"
      />
    </div>
  );
}
