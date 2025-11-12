import { TableCell, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { AtSign, ChartAreaIcon, Eye, Trash2 } from "lucide-react";
import Link from "next/link";
import type { Topic } from "@/types/topic";
import { ImageAvatar } from "@/components/brand-list";
import { deleteTopic } from "./actions";
import { LoadingButton } from "@/components/loading-button";

interface TopicTableRowProps {
  topic: Topic;
}

export function TopicTableRow({ topic }: TopicTableRowProps) {
  const handleDelete = deleteTopic.bind(null, topic.id);

  return (
    <TableRow className="hover:bg-muted/50 transition-colors">
      <TableCell>
        <Checkbox />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2 font-medium max-w-xs overflow-hidden">
          {topic.logo && <ImageAvatar title={topic.name} url={topic.logo} />}
          {topic.name}
        </div>
      </TableCell>
      <TableCell>
        <span className="font-medium max-w-xs overflow-hidden whitespace-normal break-words text-muted-foreground">
          {topic.description}
        </span>
      </TableCell>
      <TableCell>
        <span className={topic.isActive ? "text-green-600 dark:text-green-400 font-medium" : "text-muted-foreground"}>
          {topic.isActive ? "Active" : "Inactive"}
        </span>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          <Link href={`/dashboard/topics/${topic.id}`}>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 h-8 hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 dark:hover:bg-indigo-950/50 dark:hover:border-indigo-800 dark:hover:text-indigo-400 transition-all"
            >
              <ChartAreaIcon aria-label="View dashboard" className="h-4 w-4" />
            </Button>
          </Link>
          <Link href={`/dashboard/rankings/${topic.id}`}>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 h-8 hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 dark:hover:bg-indigo-950/50 dark:hover:border-indigo-800 dark:hover:text-indigo-400 transition-all"
            >
              <Eye aria-label="View rankings" className="h-4 w-4" />
            </Button>
          </Link>
          <Link href={`/dashboard/mentions/${topic.id}`}>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 h-8 hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 dark:hover:bg-indigo-950/50 dark:hover:border-indigo-800 dark:hover:text-indigo-400 transition-all"
            >
              <AtSign aria-label="View mentions" className="h-4 w-4" />
            </Button>
          </Link>
          <form action={handleDelete}>
            <LoadingButton className="hover:bg-red-50 hover:border-red-300 hover:text-red-700 dark:hover:bg-red-950/50 dark:hover:border-red-800 dark:hover:text-red-400">
              <Trash2 aria-label="Delete topic" className="h-4 w-4" />
            </LoadingButton>
          </form>
        </div>
      </TableCell>
    </TableRow>
  );
}
