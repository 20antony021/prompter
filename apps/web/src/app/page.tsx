import { Button } from '@/components/ui/button';
import { ArrowRight, BarChart3, Globe, Zap } from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <div className="font-bold text-xl">Prompter</div>
          <div className="flex gap-4">
            <Link href="/dashboard">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/dashboard">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="container flex flex-col items-center justify-center gap-4 py-24 text-center md:py-32">
        <div className="inline-block rounded-lg bg-muted px-3 py-1 text-sm">
          AI Visibility Platform
        </div>
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl">
          Get Discovered by
          <br />
          AI Assistants
        </h1>
        <p className="max-w-[700px] text-muted-foreground sm:text-xl">
          Track how ChatGPT, Claude, and Gemini mention your brand. Create
          AI-optimized pages. Measure before/after impact.
        </p>
        <div className="flex gap-4">
          <Link href="/dashboard">
            <Button size="lg">
              Start Free Trial <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Button size="lg" variant="outline">
            Watch Demo
          </Button>
        </div>
      </section>

      {/* Features */}
      <section className="border-t bg-muted/40 py-24">
        <div className="container">
          <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-3">
            <div className="flex flex-col gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <BarChart3 className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">AI Mention Tracker</h3>
              <p className="text-muted-foreground">
                Track brand mentions across multiple AI models. See sentiment,
                position, and trends over time.
              </p>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Globe className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Knowledge Pages</h3>
              <p className="text-muted-foreground">
                Generate and host AI-optimized pages. Fast, structured,
                schema-rich content.
              </p>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Zap className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Visibility Scoring</h3>
              <p className="text-muted-foreground">
                Measure your AI visibility score. Compare to competitors. Track
                improvement.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container flex justify-between">
          <div className="text-sm text-muted-foreground">
            © 2024 Prompter. All rights reserved.
          </div>
          <div className="flex gap-4 text-sm text-muted-foreground">
            <a href="/legal/privacy">Privacy</a>
            <a href="/legal/terms">Terms</a>
            <a href="/legal/aup">AUP</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

