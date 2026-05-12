import logo from "../assets/company-logo.PNG";
import { API_BASE_URL, API_ORIGIN } from "../config/api";
import type { AdminProduct } from "../types/admin";
import type { Product } from "../types";

const accentPalette = ["#ff7a00", "#f0a04b", "#0f8b8d", "#7d5a50", "#ef8354"];

function resolveImageUrl(imageUrl?: string | null): string {
  if (!imageUrl) {
    return logo;
  }
  if (imageUrl.startsWith("http")) {
    return imageUrl;
  }
  return `${API_ORIGIN}${imageUrl}`;
}

function toHeroSubtitle(description: string): string {
  const firstSentence = description.split(".").find((sentence) => sentence.trim().length > 0);
  if (!firstSentence) {
    return "Freshly managed from the admin dashboard.";
  }
  return `${firstSentence.trim()}.`;
}

function toHighlights(product: AdminProduct): string[] {
  const variantHighlights = product.variants
    .slice(0, 3)
    .map((variant) => `${variant.weight_label} available`);
  const stockHighlights = product.variants.some((variant) => variant.stock_quantity > 0)
    ? ["Ready for checkout"]
    : ["Restock soon"];

  return Array.from(new Set([product.category, ...variantHighlights, ...stockHighlights])).slice(0, 3);
}

function mapAdminProductToStorefront(product: AdminProduct, index: number): Product {
  const images = product.images.length
    ? product.images
        .sort((left, right) => left.sort_order - right.sort_order)
        .map((image) => resolveImageUrl(image.image_url))
    : [resolveImageUrl(product.image_url)];

  return {
    id: product.slug,
    name: product.name,
    flavour: product.flavour,
    accent: accentPalette[index % accentPalette.length],
    heroTitle: product.flavour,
    heroSubtitle: toHeroSubtitle(product.description),
    description: product.description,
    image: images[0],
    images,
    highlights: toHighlights(product),
    variants: product.variants.map((variant) => ({
      id: String(variant.id),
      label: variant.weight_label,
      weight: variant.weight_label,
      mrp: variant.mrp,
      sellingPrice: variant.selling_price,
      stockStatus:
        variant.stock_quantity <= 0
          ? "out_of_stock"
          : variant.stock_quantity <= 10
            ? "low_stock"
            : "in_stock"
    }))
  };
}

export async function fetchStorefrontProducts(): Promise<Product[]> {
  const response = await fetch(`${API_BASE_URL}/products`);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Unable to load products.");
  }

  const products = (await response.json()) as AdminProduct[];
  return products.map(mapAdminProductToStorefront);
}
