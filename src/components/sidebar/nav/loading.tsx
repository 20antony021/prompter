import { ChevronsUpDown } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export function NavUserLoading() {
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton size="lg" disabled>
          <Skeleton className="h-8 w-8 rounded-lg bg-accent-foreground/30" />
          <div className="grid flex-1 text-left text-sm leading-tight">
            <Skeleton className="h-4 w-20 bg-accent-foreground/30" />
            <Skeleton className="h-3 w-32 mt-1 bg-accent-foreground/30" />
          </div>
          <ChevronsUpDown className="ml-auto size-4 opacity-50" />
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
