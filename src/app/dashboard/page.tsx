import { Onboarding } from "@/components/onboarding";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

interface PageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function Page({ searchParams }: PageProps) {
  const { userId } = await auth();
  console.log("Onboarding page - userId:", userId);
  // Redirect to sign-in if not authenticated
  if (!userId) {
    redirect("/sign-in");
  }

  const params = await searchParams;
  return <Onboarding searchParams={params} />;
}
