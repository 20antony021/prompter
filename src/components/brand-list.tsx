"use client";

import { SearchResult } from "@/lib/llm";
import { cleanUrl, cn } from "@/lib/utils";
import Image from "next/image";
import { useEffect, useState } from "react";

interface BrandListProps {
  top: SearchResult[];
  className?: string;
}

// Cache last known good src per domain to keep icons stable across re-renders
const domainSrcCache = new Map<string, string>();

export function ImageAvatar({
  url,
  title,
  size = 28,
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
          "w-7 h-7 border border-gray-200 rounded object-cover shrink-0",
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
    <div className="w-7 h-7 rounded bg-gray-900 flex items-center justify-center text-xs font-medium text-gray-100 shrink-0">
      {title?.charAt(0).toUpperCase()}
    </div>
  );
}

export function BrandList({ top, className }: BrandListProps) {
  if (top.length === 0) return null;

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {top.slice(0, 3).map((brand, index) => (
        <div key={index} className="flex items-center gap-1">
          <ImageAvatar url={brand.url} title={brand.title} />
        </div>
      ))}
    </div>
  );
}
