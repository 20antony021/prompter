"use client";

import { formatRelative, format } from "date-fns";
import { useEffect, useState } from "react";

interface LocalDateProps {
  date: string | Date;
}

// This is to prevent hydration error
// https://nextjs.org/docs/messages/react-hydration-error#solution-1-using-useeffect-to-run-on-the-client-only
export function LocalDate({ date }: LocalDateProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => setIsClient(true), []);

  if (!isClient) {
    return <span>{format(new Date(date), "MMM d, yyyy")}</span>;
  }

  return <>{formatRelative(new Date(date), new Date())}</>;
}
