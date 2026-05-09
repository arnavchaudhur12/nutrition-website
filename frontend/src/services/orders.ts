import { API_BASE_URL } from "../config/api";

export type CustomerOrder = {
  order_number: string;
  status: string;
  payment_status: string;
  total_amount: number;
  customer_name: string;
  email: string;
  phone_number: string;
  delivery_address: string;
  comments?: string | null;
  items: Array<{
    product_name: string;
    flavour: string;
    variant_label: string;
    unit_price: number;
    quantity: number;
    line_total: number;
  }>;
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

