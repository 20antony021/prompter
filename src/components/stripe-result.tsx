"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Image from "next/image";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

export function StripeResult({
  success,
  canceled,
}: {
  success: boolean;
  canceled: boolean;
}) {
  const router = useRouter();

  useEffect(() => {
    if (success) {
      toast.success("Payment successful! Your subscription is now active.");
    } else if (canceled) {
      toast.error("Payment could not be processed. You can try again anytime.");
    }

    const redirectTimer = setTimeout(
      () => {
        if (success || (!success && !canceled)) {
          router.push("/dashboard");
        } else if (canceled) {
          router.push("/dashboard/pricing");
        }
      },
      success || canceled ? 3000 : 100
    );

    return () => clearTimeout(redirectTimer);
  }, [canceled, router, success]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-indigo-50/30 to-background dark:from-background dark:via-indigo-950/20 dark:to-background flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Card Container */}
        <div className="bg-card border border-border rounded-2xl shadow-2xl p-8 space-y-6">
          {/* Logo with animated ring */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-indigo-500/20 rounded-2xl blur-xl animate-pulse" />
              <div className="relative bg-gradient-to-br from-indigo-500 to-indigo-600 p-4 rounded-2xl shadow-lg">
                <Image
                  src="/logo.svg"
                  alt="Prompter"
                  width={64}
                  height={64}
                  className="object-contain"
                />
              </div>
            </div>
          </div>

          {/* Status Icon */}
          <div className="flex justify-center">
            {success && (
              <div className="relative">
                <div className="absolute inset-0 bg-green-500/20 rounded-full blur-lg" />
                <CheckCircle2 className="relative h-16 w-16 text-green-500 animate-in zoom-in duration-500" />
              </div>
            )}
            {canceled && (
              <div className="relative">
                <div className="absolute inset-0 bg-red-500/20 rounded-full blur-lg" />
                <XCircle className="relative h-16 w-16 text-red-500 animate-in zoom-in duration-500" />
              </div>
            )}
            {!success && !canceled && (
              <div className="relative">
                <div className="absolute inset-0 bg-indigo-500/20 rounded-full blur-lg" />
                <Loader2 className="relative h-16 w-16 text-indigo-600 dark:text-indigo-400 animate-spin" />
              </div>
            )}
          </div>

          {/* Message */}
          <div className="text-center space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">
              {success && "Payment Successful!"}
              {canceled && "Payment Canceled"}
              {!success && !canceled && "Processing..."}
            </h2>
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="animate-spin h-4 w-4" />
              <p className="text-sm">
                {success && "Redirecting to dashboard..."}
                {canceled && "Redirecting to pricing..."}
                {!success && !canceled && "Redirecting to dashboard..."}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="relative h-1 bg-muted rounded-full overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-indigo-600 animate-[shimmer_3s_ease-in-out_infinite]" />
          </div>
        </div>

        {/* Brand Text */}
        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            Powered by <span className="font-semibold text-indigo-600 dark:text-indigo-400">Prompter</span>
          </p>
        </div>
      </div>
    </div>
  );
}
