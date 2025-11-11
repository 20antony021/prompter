'use client';

import { SignUp } from '@clerk/nextjs';
import { useCallback, useState, type FocusEvent, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';

export default function SignUpPage() {
  const [showDetails, setShowDetails] = useState(false);
  const { isSignedIn } = useAuth();
  const router = useRouter();

  const handleFocusCapture = useCallback((e: FocusEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target instanceof HTMLInputElement) {
      if (target.type === 'email' || target.name === 'emailAddress') {
        setShowDetails(true);
      }
    }
  }, []);

  useEffect(() => {
    if (isSignedIn) {
      router.replace('/dashboard');
    }
  }, [isSignedIn, router]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-pink-50">
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-[60vmax] w-[60vmax] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(closest-side,_rgba(99,102,241,0.25),_transparent)]"></div>
      <div className="pointer-events-none absolute -top-40 -left-40 h-80 w-80 animate-blob rounded-full bg-purple-300 opacity-30 blur-3xl"></div>
      <div className="pointer-events-none animation-delay-2000 absolute -bottom-24 left-1/4 h-72 w-72 animate-blob rounded-full bg-pink-300 opacity-30 blur-3xl"></div>
      <div className="pointer-events-none animation-delay-4000 absolute -right-32 top-24 h-96 w-96 animate-blob rounded-full bg-blue-300 opacity-30 blur-3xl"></div>

      <div className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div
          className={cn('clerk-reveal', showDetails && 'show-details')}
          onFocusCapture={handleFocusCapture}
        >
          <SignUp
            path="/sign-up"
            routing="path"
            signInUrl="/sign-in"
            afterSignUpUrl="/dashboard"
            appearance={{
              elements: {
                card: 'shadow-2xl',
                headerTitle: 'text-2xl',
                headerSubtitle: 'text-muted-foreground',
                dividerRow: 'custom-divider',
                formField__emailAddress: 'email-field',
                formField__firstName: 'hidden',
                formField__lastName: 'hidden',
                formField__password: 'reveal',
                formField__confirmPassword: 'reveal',
                formButtonPrimary: 'reveal',
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}
