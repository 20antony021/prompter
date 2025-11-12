import { Suspense } from "react";
import { Table, TableBody, TableEmptyState } from "@/components/ui/table";
import { PromptsTableHeader } from "./header";
import { PromptsTableSkeleton } from "./skeleton";
import { PromptTableRow } from "./row";
import { getPrompts } from "./actions";
import { Bot } from "lucide-react";

interface PromptsTableProps {
  topicId?: string;
  searchQuery: string;
}

async function PromptsTableContent({ topicId, searchQuery }: PromptsTableProps) {
  const prompts = await getPrompts(topicId);

  // Filter prompts by content (prompt name) only
  const filteredPrompts = prompts.filter((prompt) =>
    prompt.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (filteredPrompts.length === 0) {
    return (
      <TableEmptyState
        colSpan={7}
        title={searchQuery ? "No prompts found" : "No prompts found"}
        description={
          searchQuery
            ? `No prompts match "${searchQuery}". Try a different search.`
            : "Start by creating your first prompt to see it appear here."
        }
        icon={Bot}
      />
    );
  }

  return (
    <TableBody>
      {filteredPrompts.map((prompt) => (
        <PromptTableRow key={prompt.id} prompt={prompt} />
      ))}
    </TableBody>
  );
}

export function PromptsTable({ topicId, searchQuery }: PromptsTableProps) {
  return (
    <div className="border rounded-lg overflow-hidden bg-card shadow-sm">
      <Table>
        <PromptsTableHeader />
        <Suspense key={searchQuery} fallback={<PromptsTableSkeleton />}>
          <PromptsTableContent topicId={topicId} searchQuery={searchQuery} />
        </Suspense>
      </Table>
    </div>
  );
}
