import {
  TopicsTable,
  TopicsToolbar,
  TopicsBreadcrumb,
} from "@/components/dashboard/topics";

export default function TopicsPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const q = (typeof searchParams?.q === "string" ? searchParams.q : undefined) || "";
  return (
    <>
      <TopicsBreadcrumb />
      <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
        <TopicsToolbar search={q} />
        <TopicsTable search={q} />
      </div>
    </>
  );
}
