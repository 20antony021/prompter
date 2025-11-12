import {
  RankingsBreadcrumb,
  PromptToolbar,
  PromptsTable,
} from "@/components/dashboard";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ topicId?: string }>;
  searchParams: Promise<{ q?: string }>;
}) {
  const { topicId } = await params;
  const { q } = await searchParams;
  const searchQuery = q || "";

  return (
    <>
      <RankingsBreadcrumb topicId={topicId} page="rankings" />
      <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
        <PromptToolbar topicId={topicId} />
        <PromptsTable topicId={topicId} searchQuery={searchQuery} />
      </div>
    </>
  );
}
