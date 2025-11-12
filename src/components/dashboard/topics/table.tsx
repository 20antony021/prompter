import { Suspense } from "react";
import { Table, TableBody, TableEmptyState } from "@/components/ui/table";
import { TopicsTableHeader } from "./header";
import { TopicsTableSkeleton } from "./skeleton";
import { TopicTableRow } from "./row";
import { getTopics } from "./data";
import { Bot } from "lucide-react";

interface TopicsTableProps {
  searchQuery: string;
}

async function TopicsTableContent({ searchQuery }: TopicsTableProps) {
  const topics = await getTopics();

  // Filter topics by name only
  const filteredTopics = topics.filter((topic) =>
    topic.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (filteredTopics.length === 0) {
    return (
      <TableEmptyState
        colSpan={7}
        title={searchQuery ? "No topics found" : "No topics found"}
        description={
          searchQuery
            ? `No topics match "${searchQuery}". Try a different search.`
            : "Start by creating your first topic to see it appear here."
        }
        icon={Bot}
      />
    );
  }

  return (
    <TableBody>
      {filteredTopics.map((topic) => (
        <TopicTableRow key={topic.id} topic={topic} />
      ))}
    </TableBody>
  );
}

export function TopicsTable({ searchQuery }: TopicsTableProps) {
  return (
    <div className="border rounded-lg overflow-hidden bg-card shadow-sm">
      <Table>
        <TopicsTableHeader />
        <Suspense key={searchQuery} fallback={<TopicsTableSkeleton />}>
          <TopicsTableContent searchQuery={searchQuery} />
        </Suspense>
      </Table>
    </div>
  );
}
