"use client";

import { useEffect, useState } from "react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { TopicSelectLogo, TopicSelectorSkeleton } from "../topic-selector";
import { getTopics } from "../topics/data";
import Link from "next/link";
import type { Topic } from "@/types/topic";

function TopicSelectorWrapper({ topicId }: { topicId?: string }) {
  const [topics, setTopics] = useState<Topic[]>([]);
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
    return <TopicSelectorSkeleton />;
  }

  return (
    <TopicSelectLogo
      url="/dashboard/rankings"
      topics={topics}
      currentTopicId={topicId}
    />
  );
}

export function RankingsBreadcrumb({
  topicId,
  page,
}: {
  topicId?: string;
  page: "rankings" | "results";
}) {
  return (
    <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
      <div className="flex items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <TopicSelectorWrapper topicId={topicId} />
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              {page === "rankings" ? (
                <BreadcrumbPage>Rankings</BreadcrumbPage>
              ) : (
                <Link href={`/dashboard/rankings/${topicId}`}>Rankings</Link>
              )}
            </BreadcrumbItem>
            {page === "results" && (
              <>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage>Results</BreadcrumbPage>
                </BreadcrumbItem>
              </>
            )}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </header>
  );
}
