import { API_BASE_URL, API_ORIGIN } from "../config/api";
import type { AdminProduct } from "../types/admin";

export type AdminMetrics = {
  total_orders: number;
  total_revenue: number;
  top_products: Array<[string, number]>;
  note: string;
};

export async function fetchAdminMetrics(token: string): Promise<AdminMetrics> {
  const response = await fetch(`${API_BASE_URL}/admin/metrics`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Unable to load admin dashboard.");
  }

  return (await response.json()) as AdminMetrics;
}

type ProductPayload = {
  slug: string;
  name: string;
  flavour: string;
  description: string;
  image_url?: string | null;
  category: string;
  variants: Array<{
    weight_label: string;
    mrp: number;
    selling_price: number;
    stock_quantity: number;
  }>;
};

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`
  };
}

async function parseJson<T>(response: Response, fallback: string): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? fallback);
  }

  return (await response.json()) as T;
}

export function resolveImageUrl(imageUrl?: string | null): string | null {
  if (!imageUrl) {
    return null;
  }
  if (imageUrl.startsWith("http")) {
    return imageUrl;
  }
  return `${API_ORIGIN}${imageUrl}`;
}

export async function fetchAdminProducts(token: string): Promise<AdminProduct[]> {
  const response = await fetch(`${API_BASE_URL}/admin/products`, {
    headers: authHeaders(token)
  });
  return parseJson<AdminProduct[]>(response, "Unable to load products.");
}

export async function createAdminProduct(
  token: string,
  payload: ProductPayload
): Promise<AdminProduct> {
  const response = await fetch(`${API_BASE_URL}/admin/products`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseJson<AdminProduct>(response, "Unable to create product.");
}

export async function updateAdminProduct(
  token: string,
  productId: number,
  payload: ProductPayload
): Promise<AdminProduct> {
  const response = await fetch(`${API_BASE_URL}/admin/products/${productId}`, {
    method: "PUT",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseJson<AdminProduct>(response, "Unable to update product.");
}

export async function deleteAdminProduct(token: string, productId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/products/${productId}`, {
    method: "DELETE",
    headers: authHeaders(token)
  });
  await parseJson<{ message: string }>(response, "Unable to delete product.");
}

export async function uploadAdminImage(token: string, file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/admin/upload-image`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData
  });

  const body = await parseJson<{ image_url: string }>(response, "Unable to upload image.");
  return body.image_url;
}
