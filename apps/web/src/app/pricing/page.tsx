'use client';

import { Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PLANS } from '@/lib/plans';

export default function PricingPage() {
  const planFeatures = {
    starter: [
      '1 brand',
      '30 prompts',
      '1,000 scans/month',
      '3 AI pages/month',
      '3 seats',
      '30-day data retention',
      'Email support',
    ],
    pro: [
      '3 brands',
      '150 prompts',
      '5,000 scans/month',
      '10 AI pages/month',
      '10 seats',
      '180-day data retention',
      'Email + Slack support',
    ],
    business: [
      '10 brands',
      '500 prompts',
      '15,000 scans/month',
      '25 AI pages/month',
      'Unlimited seats',
      '365-day data retention',
      'Priority support + 99.9% SLA',
    ],
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Choose the plan that fits your AI visibility needs. No hidden fees, no overages.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
          {/* Starter Plan */}
          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle>Starter</CardTitle>
              <CardDescription>Perfect for startups and small teams</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${PLANS.starter.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-3">
                {planFeatures.starter.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full" variant="outline">
                Get Started
              </Button>
            </CardFooter>
          </Card>

          {/* Pro Plan */}
          <Card className="flex flex-col border-primary shadow-lg relative">
            <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-bl-lg rounded-tr-lg">
              POPULAR
            </div>
            <CardHeader>
              <CardTitle>Pro</CardTitle>
              <CardDescription>For growing businesses with multiple brands</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${PLANS.pro.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-3">
                {planFeatures.pro.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full">
                Get Started
              </Button>
            </CardFooter>
          </Card>

          {/* Business Plan */}
          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle>Business</CardTitle>
              <CardDescription>For large teams and enterprises</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${PLANS.business.price}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-3">
                {planFeatures.business.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button className="w-full" variant="outline">
                Get Started
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Enterprise */}
        <div className="mt-12 text-center">
          <Card className="max-w-3xl mx-auto">
            <CardHeader>
              <CardTitle>Enterprise</CardTitle>
              <CardDescription>
                Custom solutions for organizations with specific requirements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-6">
                Need unlimited resources, custom integrations, or dedicated support? 
                Contact us for a custom enterprise plan tailored to your needs.
              </p>
              <Button variant="outline">Contact Sales</Button>
            </CardContent>
          </Card>
        </div>

        {/* Hard Caps Notice */}
        <div className="mt-12 text-center max-w-2xl mx-auto">
          <p className="text-sm text-muted-foreground">
            All plans include hard caps with no overages or hidden fees. 
            When you reach your monthly limit, you'll need to upgrade to continue. 
            Limits reset on the 1st of each month.
          </p>
        </div>
      </div>
    </div>
  );
}

