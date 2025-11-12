import { Toaster } from "@/components/ui/sonner";

export default function StripeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen">
      <div className="flex-1">{children}</div>
      <Toaster />
    </div>
  );
}
