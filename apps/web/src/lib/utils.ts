import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const cleanUrl = (url: string) => {
  if (!url) return "";

  const urlWithProtocol = url.startsWith("http") ? url : `https://${url}`;
  const urlObj = new URL(urlWithProtocol);
  return urlObj.hostname.toLowerCase().replace(/^www\./, "");
};

