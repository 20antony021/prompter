import { Suspense } from "react";
import { Table, TableBody, TableEmptyState } from "@/components/ui/table";
import { TopicsTableHeader } from "./header";
import { TopicsTableSkeleton } from "./skeleton";
import { TopicTableRow } from "./row";
import { getTopics } from "./data";
import { Bot } from "lucide-react";

interface TopicsTableProps {
  search?: string;
}

async function TopicsTableContent({ search = "" }: TopicsTableProps) {
  const topics = await getTopics(search);

  if (topics.length === 0) {
    return (
      <TableEmptyState
        colSpan={7}
        title="No topics found"
        description="Start by creating your first topic to see it appear here."
        icon={Bot}
      />
    );
  }

  return (
    <TableBody>
      {topics.map((topic) => (
        <TopicTableRow key={topic.id} topic={topic} />
      ))}
    </TableBody>
  );
}

export function TopicsTable({ search = "" }: TopicsTableProps) {
  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TopicsTableHeader />
        <Suspense fallback={<TopicsTableSkeleton />}>
          <TopicsTableContent search={search} />
        </Suspense>
      </Table>
    </div>
  );
}
