import { Button } from '@/components/ui/button';
import { ArrowRight, BarChart3, Target, Eye, TrendingUp } from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between">
          <div className="font-bold text-xl bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Prompter
          </div>
          <div className="flex gap-4">
            <Link href="/sign-in">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/sign-up">
              <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="container flex flex-col items-center justify-center gap-6 py-24 text-center md:py-32">
        <div className="inline-block rounded-full bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-1.5 text-sm font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
          AI Brand Monitoring Platform
        </div>
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl max-w-4xl">
          Monitor Your Brand
          <br />
          <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Across AI Platforms
          </span>
        </h1>
        <p className="max-w-[700px] text-muted-foreground text-lg sm:text-xl">
          Track how ChatGPT, Claude, and Gemini mention your brand. Analyze sentiment,
          measure visibility, and optimize your AI presence in real-time.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <Link href="/sign-up">
            <Button size="lg" className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
              Start Free Trial <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="/pricing">
            <Button size="lg" variant="outline" className="border-blue-200 hover:bg-blue-50">
              View Pricing
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="border-t bg-gradient-to-b from-white to-blue-50/30 py-24">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
              Comprehensive AI Brand Intelligence
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Everything you need to understand and improve your brand's presence in AI conversations
            </p>
          </div>
          <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-3">
            <div className="flex flex-col gap-4 p-6 rounded-lg bg-white border border-blue-100 hover:shadow-lg transition-shadow">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 text-white">
                <Target className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Brand Tracking</h3>
              <p className="text-muted-foreground">
                Monitor specific topics and brands across multiple AI models. Create targeted
                prompts with geographic precision to track regional variations.
              </p>
            </div>

            <div className="flex flex-col gap-4 p-6 rounded-lg bg-white border border-blue-100 hover:shadow-lg transition-shadow">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 text-white">
                <Eye className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Visibility Analysis</h3>
              <p className="text-muted-foreground">
                Measure your brand's visibility score across AI platforms. Track mention
                frequency, sentiment, and positioning in AI responses.
              </p>
            </div>

            <div className="flex flex-col gap-4 p-6 rounded-lg bg-white border border-blue-100 hover:shadow-lg transition-shadow">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 text-white">
                <TrendingUp className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Real-time Insights</h3>
              <p className="text-muted-foreground">
                Get instant feedback from ChatGPT, Claude, and Gemini. Compare results,
                track trends, and optimize your brand strategy.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-24 border-t">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
              Built for Modern Brands
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Whether you're a startup or enterprise, Prompter helps you stay ahead in the AI era
            </p>
          </div>
          <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-2">
            <div className="flex gap-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 shrink-0">
                <BarChart3 className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">Competitive Analysis</h3>
                <p className="text-muted-foreground text-sm">
                  Compare your brand mentions against competitors across different AI models and regions.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 shrink-0">
                <Target className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">Brand Monitoring</h3>
                <p className="text-muted-foreground text-sm">
                  Track how AI models describe your products, services, and company across different contexts.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 shrink-0">
                <Eye className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">Sentiment Tracking</h3>
                <p className="text-muted-foreground text-sm">
                  Understand the sentiment and tone of AI-generated responses about your brand.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 shrink-0">
                <TrendingUp className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-semibold mb-2">Multi-Model Coverage</h3>
                <p className="text-muted-foreground text-sm">
                  Get comprehensive coverage across OpenAI, Anthropic, and Google's AI platforms.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 py-20">
        <div className="container text-center text-white">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
            Ready to Monitor Your AI Presence?
          </h2>
          <p className="text-blue-100 text-lg max-w-2xl mx-auto mb-8">
            Start tracking your brand across AI platforms today. No credit card required.
          </p>
          <Link href="/sign-up">
            <Button size="lg" className="bg-white text-blue-600 hover:bg-blue-50">
              Get Started Free <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 bg-white">
        <div className="container flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="text-sm text-muted-foreground">
            © 2025 Prompter. All rights reserved.
          </div>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <a href="/pricing" className="hover:text-foreground transition-colors">Pricing</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="hover:text-foreground transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
