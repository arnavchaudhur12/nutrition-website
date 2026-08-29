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

export type AdminCouponOrderSummary = {
  coupon_code: string;
  orders_count: number;
  total_revenue: number;
  total_products_sold: number;
  order_numbers: string;
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

export async function fetchAdminCouponOrders(
  token: string,
  period: AdminDashboardPeriod
): Promise<AdminCouponOrderSummary[]> {
  const response = await fetch(
    `${API_BASE_URL}/admin/coupon-orders?period=${encodeURIComponent(period)}`,
    {
      headers: authHeaders(token)
    }
  );
  return parseJson<AdminCouponOrderSummary[]>(response, "Unable to load coupon-wise orders.");
}

export async function downloadInvoiceStatement(
  token: string,
  startDate: string,
  endDate: string
): Promise<{ blob: Blob; filename: string }> {
  const response = await fetch(
    `${API_BASE_URL}/admin/invoice-statement/download?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`,
    {
      headers: authHeaders(token)
    }
  );

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Unable to download invoice statement.");
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="([^"]+)"/i);
  return {
    blob: await response.blob(),
    filename: match?.[1] ?? `invoice-statement-${startDate}-to-${endDate}.pdf`
  };
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

const MAX_UPLOAD_BYTES = 9 * 1024 * 1024;
const RESIZABLE_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

async function prepareImageForUpload(file: File): Promise<File> {
  if (file.size <= MAX_UPLOAD_BYTES || !RESIZABLE_IMAGE_TYPES.has(file.type)) {
    return file;
  }

  const image = await loadImage(file);
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  if (!context) {
    return file;
  }

  const maxDimension = 2400;
  const scale = Math.min(1, maxDimension / Math.max(image.naturalWidth, image.naturalHeight));
  canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
  canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
  context.drawImage(image, 0, 0, canvas.width, canvas.height);

  for (const quality of [0.86, 0.78, 0.7]) {
    const blob = await canvasToBlob(canvas, "image/jpeg", quality);
    if (blob.size <= MAX_UPLOAD_BYTES || quality === 0.7) {
      const filename = file.name.replace(/\.[^.]+$/, "") || "upload";
      return new File([blob], `${filename}.jpg`, { type: "image/jpeg" });
    }
  }

  return file;
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Unable to read the selected image."));
    };
    image.src = url;
  });
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob);
          return;
        }
        reject(new Error("Unable to prepare image for upload."));
      },
      type,
      quality
    );
  });
}

export async function uploadAdminImage(token: string, file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", await prepareImageForUpload(file));

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
