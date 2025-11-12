"use client";

import { ChevronsUpDown, CreditCard, Sparkles } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { NavUserLoading } from "./loading";
import { useEffect, useState } from "react";
import { UpgradeButton } from "@/components/upgrade-button";
import { PlanType } from "@/lib/stripe/server";
import { manageSubscription } from "@/app/actions/stripe";
import { LoadingButton } from "@/components/loading-button";
import { SignOutButton } from "./sign-out-button";
import { useUser } from "@clerk/nextjs";

type UserData = {
  id: string;
  name: string;
  email: string;
  image: string | null;
  plan: PlanType;
  stripeCustomerId: string | null;
};

export function NavUser() {
  const { user, isLoaded } = useUser();
  const [userData, setUserData] = useState<UserData | null>(null);

  useEffect(() => {
    async function fetchUserData() {
      if (!user) return;

      try {
        const response = await fetch("/api/user/plan");
        if (response.ok) {
          const data = await response.json();
          setUserData({
            id: user.id,
            name: user.fullName || user.primaryEmailAddress?.emailAddress || "User",
            email: user.primaryEmailAddress?.emailAddress || "",
            image: user.imageUrl,
            plan: data.plan || "free",
            stripeCustomerId: data.stripeCustomerId || null,
          });
        }
      } catch (error) {
        console.error("Failed to fetch user data:", error);
      }
    }

    if (isLoaded && user) {
      fetchUserData();
    }
  }, [user, isLoaded]);

  if (!isLoaded || !user || !userData) {
    return <NavUserLoading />;
  }

  return <NavUserComp user={userData} />;
}

export function NavUserComp({
  user,
}: {
  user: UserData;
}) {
  const currentPlan: PlanType = user.plan;
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <Avatar className="h-8 w-8 rounded-lg">
                <AvatarImage src={user.image ?? ""} alt={user.name} />
                <AvatarFallback className="rounded-lg">
                  {user.name.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{user.name}</span>
                <span className="truncate text-xs">{user.email}</span>
              </div>
              <ChevronsUpDown className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
            side="right"
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="p-0 font-normal">
              <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                <Avatar className="h-8 w-8 rounded-lg">
                  <AvatarImage src={user.image ?? ""} alt={user.name} />
                  <AvatarFallback className="rounded-lg">
                    {user.name.charAt(0)}
                  </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{user.name}</span>
                  <span className="truncate text-xs">{user.email}</span>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {!["pro", "enterprise"].includes(currentPlan) && (
              <>
                <DropdownMenuGroup>
                  <DropdownMenuItem className="p-0">
                    <UpgradeButton
                      planType={currentPlan === "free" ? "basic" : "pro"}
                      size="sm"
                      variant="ghost"
                    >
                      <Sparkles className="h-4 w-4" />
                      {currentPlan === "free"
                        ? "Upgrade to Basic"
                        : "Upgrade to Pro"}
                    </UpgradeButton>
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
              </>
            )}
            <DropdownMenuGroup>
              <DropdownMenuItem className="p-0">
                <form action={manageSubscription} className="w-full">
                  <LoadingButton
                    type="submit"
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start gap-2"
                  >
                    <CreditCard className="h-4 w-4" />
                    Manage Subscription
                  </LoadingButton>
                </form>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <SignOutButton />
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
