import { API_BASE_URL, API_ORIGIN } from "../config/api";
import type { HeroConfig } from "../types/hero";

export function resolveHeroImageUrl(imageUrl?: string | null): string | null {
  if (!imageUrl) {
    return null;
  }
  if (imageUrl === "/hero-quote-background.jpeg") {
    return imageUrl;
  }
  if (imageUrl.startsWith("http")) {
    return imageUrl;
  }
  return `${API_ORIGIN}${imageUrl}`;
}

export async function fetchHeroConfig(): Promise<HeroConfig> {
  const response = await fetch(`${API_BASE_URL}/hero`);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Unable to load hero settings.");
  }

  return (await response.json()) as HeroConfig;
}
