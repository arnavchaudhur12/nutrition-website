import logo from "../assets/company-logo.PNG";
import { API_BASE_URL, API_ORIGIN } from "../config/api";
import type { AdminProduct } from "../types/admin";
import type { Product } from "../types";

const accentPalette = ["#ff7a00", "#f0a04b", "#0f8b8d", "#7d5a50", "#ef8354"];
const darkChocolateImages = [
  new URL("../../../all_images/peanut_butter/product_1/1C.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_1/2C.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_1/3C.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_1/4C.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_1/5C.jpg", import.meta.url).href
];
const mawaMalaiImages = [
  new URL("../../../all_images/peanut_butter/product_2/1M.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_2/2M.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_2/3M.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_2/4M.jpg", import.meta.url).href,
  new URL("../../../all_images/peanut_butter/product_2/5M.jpg", import.meta.url).href
];

function getBundledProductImages(product: AdminProduct): string[] {
  const slug = product.slug.trim().toLowerCase();
  const flavour = product.flavour.trim().toLowerCase();

  if (slug === "dark-chocolate-crispy" || flavour === "dark chocolate crispy") {
    return darkChocolateImages;
  }

  if (slug === "mawa-malai-creamy" || flavour === "mawa malai creamy") {
    return mawaMalaiImages;
  }

  return [];
}

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
  const inStockVariants = product.variants.filter((variant) => variant.stock_quantity > 0);
  const variantHighlights = product.variants
    .filter((variant) => variant.stock_quantity > 0)
    .slice(0, 3)
    .map((variant) => `${variant.weight_label} available`);
  const stockHighlights = inStockVariants.length > 0
    ? ["Ready for checkout"]
    : ["Restock soon"];

  return Array.from(new Set([product.category, ...variantHighlights, ...stockHighlights])).slice(0, 3);
}

function getFullProductName(product: AdminProduct): string {
  const name = product.name.trim();
  const flavour = product.flavour.trim();
  if (!flavour || name.toLowerCase().includes(flavour.toLowerCase())) {
    return name;
  }
  return `${name} - ${flavour}`;
}

function mapAdminProductToStorefront(product: AdminProduct, index: number): Product {
  const uploadedImages = product.images.length
    ? product.images
        .sort((left, right) => left.sort_order - right.sort_order)
        .map((image) => resolveImageUrl(image.image_url))
    : product.image_url
      ? [resolveImageUrl(product.image_url)]
      : [];
  const bundledImages = getBundledProductImages(product);
  const images = bundledImages.length > 0 ? bundledImages : uploadedImages.length > 0 ? uploadedImages : [logo];

  return {
    id: product.slug,
    name: product.name,
    flavour: product.flavour,
    fullName: getFullProductName(product),
    accent: accentPalette[index % accentPalette.length],
    heroTitle: getFullProductName(product),
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
      stockQuantity: variant.stock_quantity,
      discountPercentage:
        variant.mrp > variant.selling_price
          ? Math.round(((variant.mrp - variant.selling_price) / variant.mrp) * 100)
          : 0,
      stockStatus:
        variant.stock_quantity <= 0
          ? "out_of_stock"
          : variant.stock_quantity <= 15
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
