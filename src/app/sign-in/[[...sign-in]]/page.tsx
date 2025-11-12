"use client";

import { SignIn } from "@clerk/nextjs";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function SignInPage() {
  const { isSignedIn } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isSignedIn) {
      router.replace("/dashboard");
    }
  }, [isSignedIn, router]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="pointer-events-none absolute -top-40 -left-40 h-96 w-96 rounded-full bg-blue-300 opacity-20 blur-3xl"></div>
      <div className="pointer-events-none absolute -bottom-32 -right-24 h-96 w-96 rounded-full bg-indigo-300 opacity-20 blur-3xl"></div>
      <div className="flex min-h-screen items-center justify-center p-4">
        <SignIn
          appearance={{
            elements: {
              card: "shadow-2xl",
              headerTitle: "text-2xl",
              headerSubtitle: "text-muted-foreground",
            },
          }}
        />
      </div>
    </div>
  );
}
