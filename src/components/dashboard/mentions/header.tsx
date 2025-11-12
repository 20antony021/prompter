import { TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Target,
  TrendingUp,
  MessageSquare,
  Bot,
  Calendar,
  Hash,
  FileText,
} from "lucide-react";

export function MentionsTableHeader() {
  return (
    <TableHeader>
      <TableRow className="hover:bg-transparent border-b bg-muted/50">
        <TableHead>
          <Checkbox />
        </TableHead>
        <TableHead className="w-1/8 font-semibold">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Topic
          </div>
        </TableHead>
        <TableHead className="w-1/8 font-semibold">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Type
          </div>
        </TableHead>
        <TableHead className="w-1/8 font-semibold">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Sentiment
          </div>
        </TableHead>
        <TableHead className="font-semibold">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Extracted Text
          </div>
        </TableHead>
        <TableHead className="w-1/8 font-semibold">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Model
          </div>
        </TableHead>
        <TableHead className="w-1/8 font-semibold">
          <div className="flex items-center gap-2">
            <Hash className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Position
          </div>
        </TableHead>
        <TableHead className="w-1/8 font-semibold">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Created
          </div>
        </TableHead>
      </TableRow>
    </TableHeader>
  );
}
