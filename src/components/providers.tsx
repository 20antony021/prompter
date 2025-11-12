'use client';

import { ClerkProvider } from '@clerk/nextjs';
import { Toaster } from '@/components/ui/sonner';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      afterSignInUrl="/dashboard"
      afterSignUpUrl="/dashboard"
      localization={{
        formFieldLabel__emailAddress: 'Work email',
        formFieldInputPlaceholder__emailAddress: 'name@company.com',
      }}
    >
      {children}
      <Toaster />
    </ClerkProvider>
  );
}
