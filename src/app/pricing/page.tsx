'use client';

import { Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PLANS } from '@/lib/stripe/server';
import Link from 'next/link';
import { useAuth } from '@clerk/nextjs';

export default function PricingPage() {
  const { isSignedIn } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-blue-50/30">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="font-bold text-xl bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Prompter
          </Link>
          <div className="flex gap-4">
            {!isSignedIn ? (
              <>
                <Link href="/sign-in">
                  <Button variant="ghost">Sign In</Button>
                </Link>
                <Link href="/sign-up">
                  <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                    Get Started
                  </Button>
                </Link>
              </>
            ) : (
              <Link href="/dashboard">
                <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                  Go to Dashboard
                </Button>
              </Link>
            )}
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Choose the plan that fits your AI brand monitoring needs. No hidden fees.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-8 md:grid-cols-4 max-w-7xl mx-auto mb-12">
          {/* Free Plan */}
          <Card className="flex flex-col border-blue-100">
            <CardHeader>
              <CardTitle>Free</CardTitle>
              <CardDescription>Perfect for getting started</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${PLANS.free.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-3">
                {PLANS.free.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full" variant="outline" asChild>
                <Link href={isSignedIn ? '/dashboard' : '/sign-up'}>Get Started</Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Basic Plan */}
          <Card className="flex flex-col border-blue-100">
            <CardHeader>
              <CardTitle>Basic</CardTitle>
              <CardDescription>For small teams and startups</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${PLANS.basic.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-3">
                {PLANS.basic.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full" variant="outline" asChild>
                <Link href={isSignedIn ? '/dashboard/pricing' : '/sign-up'}>Get Started</Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Pro Plan */}
          <Card className="flex flex-col border-orange-600 shadow-lg relative">
            <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-orange-600 text-white text-xs font-semibold px-3 py-1 rounded">
              Most Popular
            </div>
            <CardHeader>
              <CardTitle>Professional</CardTitle>
              <CardDescription>For growing businesses</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${PLANS.pro.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-3">
                {PLANS.pro.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full bg-orange-600 hover:bg-orange-700 text-white" asChild>
                <Link href={isSignedIn ? '/dashboard/pricing' : '/sign-up'}>Get Started</Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Enterprise Plan */}
          <Card className="flex flex-col border-blue-100">
            <CardHeader>
              <CardTitle>Enterprise</CardTitle>
              <CardDescription>For large organizations</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${PLANS.enterprise.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-3">
                {PLANS.enterprise.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full" variant="outline" asChild>
                <Link href={isSignedIn ? '/dashboard/pricing' : '/sign-up'}>Get Started</Link>
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Footer Notice */}
        <div className="mt-12 text-center max-w-2xl mx-auto">
          <p className="text-sm text-muted-foreground">
            All plans include SSL security, 99.9% uptime, and email support.
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            You can cancel or change your plan at any time.
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t py-12 bg-white mt-16">
        <div className="container flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="text-sm text-muted-foreground">
            © 2025 Prompter. All rights reserved.
          </div>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="hover:text-foreground transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
