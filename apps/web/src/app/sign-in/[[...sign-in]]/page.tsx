"use client";

import { SignIn } from "@clerk/nextjs";
import { useAuth } from "@clerk/nextjs";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SignInPage() {
  const { isSignedIn } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isSignedIn) {
      router.replace("/dashboard");
    }
  }, [isSignedIn, router]);
  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-pink-50">
      <div className="pointer-events-none absolute -top-40 -left-40 h-96 w-96 rounded-full bg-purple-300 opacity-20 blur-3xl"></div>
      <div className="pointer-events-none absolute -bottom-32 -right-24 h-96 w-96 rounded-full bg-blue-300 opacity-20 blur-3xl"></div>
      <div className="flex min-h-screen items-center justify-center p-4">
        <SignIn
          path="/sign-in"
          routing="path"
          afterSignInUrl="/dashboard"
          signUpUrl="/sign-up"
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
