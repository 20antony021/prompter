"use client";

import { cleanUrl, cn } from "@/lib/utils";
import Image from "next/image";
import { useEffect, useState } from "react";

// Cache last known good src per domain to keep icons stable across re-renders
const domainSrcCache = new Map<string, string>();

export function ImageAvatar({
  url,
  title,
  size = 80,
  className,
}: {
  url: string;
  title: string;
  size?: number;
  className?: string;
}) {
  const link = cleanUrl(url);
  const [failed, setFailed] = useState(false); // track final failure
  const [src, setSrc] = useState<string | null>(
    link ? domainSrcCache.get(link) || `https://logo.clearbit.com/${link}` : null
  );

  useEffect(() => {
    // Reset when the domain changes
    setFailed(false);
    setSrc(link ? domainSrcCache.get(link) || `https://logo.clearbit.com/${link}` : null);
  }, [link]);

  if (link && src && !failed) {
    return (
      <Image
        src={src}
        alt={title}
        className={cn(
          "w-6.5 h-6.5 border border-gray-200 rounded object-cover",
          className
        )}
        width={size}
        height={size}
        unoptimized
        onLoad={() => {
          if (src) domainSrcCache.set(link, src);
        }}
        onError={() => {
          // Fallback chain: Clearbit -> DuckDuckGo -> letter avatar
          if (src.includes("logo.clearbit.com")) {
            const fb = `https://icons.duckduckgo.com/ip3/${link}.ico`;
            domainSrcCache.set(link, fb);
            setSrc(fb);
          } else {
            setFailed(true);
          }
        }}
      />
    );
  }

  return (
    <div className="w-6 h-6 rounded bg-gray-900 flex items-center justify-center text-xs font-medium text-gray-100">
      {title?.charAt(0).toUpperCase()}
    </div>
  );
}
