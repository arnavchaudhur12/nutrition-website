import { API_BASE_URL } from "../config/api";

export type CustomerOrder = {
  order_number: string;
  status: string;
  payment_status: string;
  total_amount: number;
  customer_name: string;
  email: string;
  phone_number: string;
  alternate_phone_number?: string | null;
  delivery_address: string;
  pincode: string;
  city: string;
  state: string;
  comments?: string | null;
  items: Array<{
    product_name: string;
    flavour: string;
    variant_label: string;
    unit_price: number;
    quantity: number;
    line_total: number;
  }>;
  shipment?: {
    provider: string;
    order_id?: string | null;
    awb_number?: string | null;
    status?: string | null;
    courier?: string | null;
    label_url?: string | null;
    estimated_delivery?: string | null;
    error?: string | null;
    last_synced_at?: string | null;
    history: Array<{
      status: string;
      location?: string | null;
      timestamp?: string | null;
    }>;
  } | null;
};

export async function fetchMyOrders(token: string): Promise<CustomerOrder[]> {
  const response = await fetch(`${API_BASE_URL}/orders/my`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Unable to load your orders.");
  }

  return (await response.json()) as CustomerOrder[];
}
