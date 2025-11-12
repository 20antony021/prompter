import {
  TopicsTable,
  TopicsToolbar,
  TopicsBreadcrumb,
} from "@/components/dashboard";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  const searchQuery = q || "";

  return (
    <>
      <TopicsBreadcrumb />
      <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
        <TopicsToolbar />
        <TopicsTable searchQuery={searchQuery} />
      </div>
    </>
  );
}
