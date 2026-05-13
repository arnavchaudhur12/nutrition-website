import { API_BASE_URL } from "../config/api";

export type CreatePaymentOrderPayload = {
  amount?: number;
  currency?: string;
  receipt?: string;
  customer_name?: string;
  email?: string;
  phone_number?: string;
  alternate_phone_number?: string;
  delivery_address?: string;
  comments?: string;
  items?: Array<{
    product_slug: string;
    variant_id: number;
    quantity: number;
  }>;
};

export type PaymentOrder = {
  order_id: string;
  amount: number;
  currency: string;
  receipt?: string | null;
  app_order_number?: string | null;
};

export type VerifyPaymentPayload = {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
};

export type VerifyPaymentResult = {
  success: boolean;
  order_number?: string | null;
};

async function parseError(response: Response, fallback: string): Promise<Error> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return new Error(body?.detail ?? fallback);
}

export async function createPaymentOrder(payload: CreatePaymentOrderPayload): Promise<PaymentOrder> {
  const response = await fetch(`${API_BASE_URL}/create-order`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw await parseError(response, "Unable to start payment.");
  }

  return (await response.json()) as PaymentOrder;
}

export async function verifyPayment(payload: VerifyPaymentPayload): Promise<VerifyPaymentResult> {
  const response = await fetch(`${API_BASE_URL}/verify-payment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw await parseError(response, "Payment verification failed.");
  }

  return (await response.json()) as VerifyPaymentResult;
}
