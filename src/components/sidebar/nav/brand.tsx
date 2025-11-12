"use client";

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import Image from "next/image";
import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";

export function BrandComp() {
  const { user } = useUser();
  const [userPlan, setUserPlan] = useState<string>("free");

  useEffect(() => {
    // Fetch user plan from server action
    async function fetchUserPlan() {
      try {
        const response = await fetch("/api/user/plan");
        if (response.ok) {
          const data = await response.json();
          setUserPlan(data.plan || "free");
        }
      } catch (error) {
        console.error("Failed to fetch user plan:", error);
      }
    }

    if (user) {
      fetchUserPlan();
    }
  }, [user]);

  const planDisplay = userPlan.charAt(0).toUpperCase() + userPlan.slice(1);

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size="lg"
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
        >
          <div className="flex aspect-square size-8 items-center justify-center rounded-lg mr-1">
            <Image
              src="/logo.svg"
              alt="Prompter"
              className="size-8 object-contain rounded-lg"
              width={32}
              height={32}
            />
          </div>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-semibold">Prompter</span>
            <span className="truncate text-xs capitalize">
              {planDisplay} Plan
            </span>
          </div>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
