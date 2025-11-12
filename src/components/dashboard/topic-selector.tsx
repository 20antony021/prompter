"use client";

import Link from "next/link";
import { SquareDashed, Search } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { Topic } from "@/types/topic";
import { Skeleton } from "@/components/ui/skeleton";
import { ImageAvatar } from "@/components/brand-list";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getTopics } from "./topics/data";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";

interface TopicSelectorProps {
  topics: Topic[];
  currentTopicId?: string;
  placeholder?: string;
  url: string;
}

export function TopicSelectorSkeleton() {
  return <Skeleton className="w-6.5 h-6.5 rounded" />;
}

export function TopicSelectLogo({
  topics,
  currentTopicId,
  url,
}: TopicSelectorProps) {
  const selectedTopic = topics.find((topic) => topic.id === currentTopicId);
  const [searchQuery, setSearchQuery] = useState("");

  // Filter topics by name only
  const filteredTopics = topics.filter((topic) =>
    topic.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Popover>
      <PopoverTrigger className="flex items-center gap-1">
        {selectedTopic?.logo ? (
          <ImageAvatar url={selectedTopic.logo} title={selectedTopic.name} />
        ) : (
          <span className="bg-muted-foreground/10 rounded w-6.5 h-6.5 flex border border-border items-center justify-center">
            <SquareDashed className="h-4 w-4 text-muted-foreground" />
          </span>
        )}
      </PopoverTrigger>
      <PopoverContent className="p-0 w-64" align="start">
        <div className="p-2 border-b">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 pl-8 text-sm border-border bg-background/50"
            />
          </div>
        </div>
        <div className="max-h-[300px] overflow-y-auto">
          {filteredTopics.length === 0 ? (
            <div className="p-3 text-sm text-muted-foreground text-center">
              {searchQuery ? `No topics match "${searchQuery}"` : "No topics available"}
            </div>
          ) : (
            filteredTopics.map((topic) => (
              <Link
                key={topic.id}
                href={`${url}/${topic.id}`}
                prefetch={false}
                className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors border-b last:border-b-0"
              >
                {topic.logo && (
                  <ImageAvatar url={topic.logo} title={topic.name} />
                )}
                <span className="truncate">{topic.name}</span>
              </Link>
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

export async function TopicSelect({
  label,
  currentTopicId,
}: {
  label: string;
  currentTopicId?: string;
}) {
  const topics = await getTopics();

  return (
    <div className="grid gap-2">
      <label htmlFor="topicId" className="text-sm font-semibold text-foreground">
        {label}
      </label>
      <Select name="topicId" required defaultValue={currentTopicId}>
        <SelectTrigger className="w-full sm:w-[180px]">
          <SelectValue placeholder="Select a topic..." />
        </SelectTrigger>
        <SelectContent>
          {topics.map((topic) => (
            <SelectItem key={topic.id} value={topic.id}>
              {topic.logo && (
                <ImageAvatar url={topic.logo} title={topic.name} />
              )}
              <span className="truncate">{topic.name}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

// Client-side version for use in client components (like dialogs)
export function TopicSelectClient({
  label,
  currentTopicId,
}: {
  label: string;
  currentTopicId?: string;
}) {
  const [topics, setTopics] = useState<Pick<Topic, 'id' | 'name' | 'logo' | 'description'>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTopics() {
      try {
        const data = await getTopics();
        setTopics(data);
      } catch (error) {
        console.error("Failed to fetch topics:", error);
        setTopics([]);
      } finally {
        setLoading(false);
      }
    }
    fetchTopics();
  }, []);

  if (loading) {
    return (
      <div className="grid gap-2">
        <label htmlFor="topicId" className="text-sm font-semibold text-foreground">
          {label}
        </label>
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  return (
    <div className="grid gap-2">
      <label htmlFor="topicId" className="text-sm font-semibold text-foreground">
        {label}
      </label>
      <Select name="topicId" required defaultValue={currentTopicId}>
        <SelectTrigger className="w-full sm:w-[180px]">
          <SelectValue placeholder="Select a topic..." />
        </SelectTrigger>
        <SelectContent>
          {topics.map((topic) => (
            <SelectItem key={topic.id} value={topic.id}>
              {topic.logo && (
                <ImageAvatar url={topic.logo} title={topic.name} />
              )}
              <span className="truncate">{topic.name}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
