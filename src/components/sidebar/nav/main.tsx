"use client";

import { AtSign, Bot, Tag } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import Link from "next/link";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const staticNavMain = [
  {
    title: "Topics",
    icon: Tag,
    url: "/dashboard/topics",
  },
  {
    title: "Rankings",
    icon: Bot,
    url: "/dashboard/rankings",
  },
  {
    title: "Mentions",
    icon: AtSign,
    url: "/dashboard/mentions",
  },
];

export function NavMain() {
  const pathname = usePathname();
  const { state } = useSidebar();

  return (
    <SidebarGroup>
      <SidebarMenu>
        {staticNavMain.map((item) => {
          const isActive =
            pathname === item.url || pathname.startsWith(item.url + "/");

          const buttonContent = (
            <SidebarMenuButton
              asChild
              size="lg"
              className={cn(
                "py-6",
                state === "collapsed" ? "px-0 justify-center" : "px-4",
                "text-base transition-all",
                isActive
                  ? "bg-indigo-600 text-white hover:bg-indigo-700 hover:text-white"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Link href={item.url}>
                <item.icon className="h-5 w-5 shrink-0" />
                {state === "expanded" && <span>{item.title}</span>}
              </Link>
            </SidebarMenuButton>
          );

          if (state === "collapsed") {
            return (
              <SidebarMenuItem key={item.title}>
                <TooltipProvider delayDuration={0}>
                  <Tooltip>
                    <TooltipTrigger asChild>{buttonContent}</TooltipTrigger>
                    <TooltipContent side="right" className="font-medium">
                      {item.title}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </SidebarMenuItem>
            );
          }

          return <SidebarMenuItem key={item.title}>{buttonContent}</SidebarMenuItem>;
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}
