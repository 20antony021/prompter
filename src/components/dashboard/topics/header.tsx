import { TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { MessageSquare, Eye, Settings, Check } from "lucide-react";

export function TopicsTableHeader() {
  return (
    <TableHeader>
      <TableRow className="hover:bg-transparent border-b bg-muted/50">
        <TableHead>
          <Checkbox />
        </TableHead>
        <TableHead className="w-1/6 font-semibold">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Topic
          </div>
        </TableHead>
        <TableHead className="font-semibold">
          <div className="flex items-center gap-2">
            <Eye className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Description
          </div>
        </TableHead>
        <TableHead className="w-1/6 font-semibold">
          <div className="flex items-center gap-2">
            <Check className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Active
          </div>
        </TableHead>
        <TableHead className="w-1/6 font-semibold">
          <div className="flex items-center gap-2">
            <Settings className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            Actions
          </div>
        </TableHead>
      </TableRow>
    </TableHeader>
  );
}
