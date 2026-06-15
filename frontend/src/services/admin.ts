import { API_BASE_URL, API_ORIGIN } from "../config/api";
import type { HeroConfig } from "../types/hero";
import type { AdminProduct } from "../types/admin";

export type AdminMetrics = {
  total_actual_sales_count: number;
  total_actual_revenue: number;
  total_products_sold: number;
  product_performance: Array<{
    product_name: string;
    quantity_sold: number;
    total_amount: number;
  }>;
  note: string;
};

export type AdminDashboardPeriod =
  | "all_time"
  | "last_7_days"
  | "last_30_days"
  | "last_90_days";

export type AdminCustomerPortfolio = {
  order_number: string;
  created_at: string;
  customer_name: string;
  delivery_address: string;
  payment_mode: string;
  only_success: boolean;
  amount_count: number;
  products: string;
  product_quantity: number;
  product_count: number;
  phone_number: string;
  email: string;
  status: string;
  payment_status: string;
};

export type CouponCode = {
  id: number;
  code: string;
  discount_percent: number;
  created_at: string;
};

export async function fetchAdminMetrics(
  token: string,
  period: AdminDashboardPeriod
): Promise<AdminMetrics> {
  const response = await fetch(`${API_BASE_URL}/admin/metrics?period=${encodeURIComponent(period)}`, {
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

export async function fetchAdminCustomerPortfolio(
  token: string,
  period: AdminDashboardPeriod
): Promise<AdminCustomerPortfolio[]> {
  const response = await fetch(
    `${API_BASE_URL}/admin/customer-portfolio?period=${encodeURIComponent(period)}`,
    {
    headers: authHeaders(token)
    }
  );
  return parseJson<AdminCustomerPortfolio[]>(response, "Unable to load customer portfolio.");
}

type ProductPayload = {
  slug: string;
  name: string;
  flavour: string;
  description: string;
  image_url?: string | null;
  image_urls: string[];
  category: string;
  variants: Array<{
    weight_label: string;
    mrp: number;
    selling_price: number;
    stock_quantity: number;
  }>;
};

export type HeroPayload = {
  eyebrow_text: string;
  headline: string;
  body_text: string;
  cta_label: string;
  cta_link: string;
  offer_text: string;
  badge_title: string;
  badge_subtitle: string;
  image_urls: string[];
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
  if (imageUrl === "/hero-quote-background.jpeg") {
    return imageUrl;
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

export async function fetchAdminHero(token: string): Promise<HeroConfig> {
  const response = await fetch(`${API_BASE_URL}/admin/hero`, {
    headers: authHeaders(token)
  });
  return parseJson<HeroConfig>(response, "Unable to load hero settings.");
}

export async function updateAdminHero(token: string, payload: HeroPayload): Promise<HeroConfig> {
  const response = await fetch(`${API_BASE_URL}/admin/hero`, {
    method: "PUT",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseJson<HeroConfig>(response, "Unable to update hero settings.");
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

export async function fetchAdminCoupons(token: string): Promise<CouponCode[]> {
  const response = await fetch(`${API_BASE_URL}/admin/coupons`, {
    headers: authHeaders(token)
  });
  return parseJson<CouponCode[]>(response, "Unable to load coupon codes.");
}

export async function createAdminCoupon(
  token: string,
  payload: { code: string; discount_percent: number }
): Promise<CouponCode> {
  const response = await fetch(`${API_BASE_URL}/admin/coupons`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseJson<CouponCode>(response, "Unable to create coupon code.");
}

export async function deleteAdminCoupon(token: string, code: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/coupons/${encodeURIComponent(code)}`, {
    method: "DELETE",
    headers: authHeaders(token)
  });
  await parseJson<{ message: string }>(response, "Unable to delete coupon code.");
}
