import { Button } from "@/components/ui/button";
import { Plus, Lightbulb } from "lucide-react";
import { CreatePromptDialog } from "./create-dialog";
import { SuggestionsDialog } from "./suggestions-dialog";
import { RankingsSearchBox } from "./search-box";

interface PromptToolbarProps {
  topicId?: string;
}

export function PromptToolbar({ topicId }: PromptToolbarProps) {
  return (
    <div className="flex items-center justify-between flex-col gap-2 sm:flex-row">
      <RankingsSearchBox />
      <div className="flex items-center gap-2 w-full sm:w-auto">
        <CreatePromptDialog>
          <Button
            size="sm"
            className="gap-2 flex-1 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm h-10 px-4"
          >
            <Plus className="h-4 w-4" />
            Add Prompt
          </Button>
        </CreatePromptDialog>
        <SuggestionsDialog topicId={topicId}>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 flex-1 border-indigo-200 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-300 dark:border-indigo-800 dark:text-indigo-400 dark:hover:bg-indigo-950/50 h-10 px-4"
          >
            <Lightbulb className="h-4 w-4" />
            Suggestions
          </Button>
        </SuggestionsDialog>
      </div>
    </div>
  );
}
