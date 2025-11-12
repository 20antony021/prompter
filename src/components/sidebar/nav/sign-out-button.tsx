'use client';

import { LogOut } from "lucide-react";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { useClerk } from "@clerk/nextjs";

export function SignOutButton() {
  const { signOut } = useClerk();

  const handleSignOut = async () => {
    await signOut();
    // Force a full page reload to ensure clean state
    window.location.href = '/';
  };

  return (
    <DropdownMenuItem
      onClick={handleSignOut}
      className="cursor-pointer"
    >
      <LogOut className="h-4 w-4" />
      Log out
    </DropdownMenuItem>
  );
}
