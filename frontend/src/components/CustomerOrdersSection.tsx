import type { CustomerOrder } from "../services/orders";

type CustomerOrdersSectionProps = {
  orders: CustomerOrder[];
  loading?: boolean;
  error?: string;
  title?: string;
  emptyMessage?: string;
  mode?: "history" | "tracking";
};

function formatShipmentDate(value?: string | null): string {
  if (!value) {
    return "Awaiting update";
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium"
  }).format(new Date(value));
}

function formatShipmentDateTime(value?: string | null): string {
  if (!value) {
    return "Live sync pending";
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function formatOrderTotal(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(amount);
}

function getShipmentTone(order: CustomerOrder): "pending" | "active" | "delivered" | "error" {
  const status = order.shipment?.status?.toLowerCase() ?? "";
  if (order.shipment?.error) {
    return "error";
  }
  if (status.includes("pending") || status.includes("created")) {
    return "pending";
  }
  if (status.includes("delivered")) {
    return "delivered";
  }
  if (status || order.shipment?.awb_number) {
    return "active";
  }
  return "pending";
}

function getShipmentStepIndex(order: CustomerOrder): number {
  const status = order.shipment?.status?.toLowerCase() ?? "";
  if (status.includes("delivered")) return 4;
  if (status.includes("out for delivery")) return 3;
  if (status.includes("transit") || status.includes("hub") || status.includes("picked")) return 2;
  if (status.includes("pending") || status.includes("placed") || status.includes("confirmed")) return 1;
  if (order.shipment?.awb_number || order.shipment?.order_id) return 1;
  if (order.payment_status === "paid") return 0;
  return -1;
}

function getShipmentTimeline(order: CustomerOrder) {
  const stepIndex = getShipmentStepIndex(order);
  const hasShipment = Boolean(order.shipment);

  return [
    {
      label: "Payment Confirmed",
      detail: order.payment_status === "paid" ? "Your order is locked in." : "Waiting for payment confirmation.",
      done: order.payment_status === "paid",
      active: stepIndex < 0 && order.payment_status !== "paid"
    },
    {
      label: "Shipment Created",
      detail: hasShipment
        ? order.shipment?.message
          ? order.shipment.message
          : order.shipment?.order_id
            ? `Shipment ${order.shipment.order_id} created.`
            : "Courier partner assignment is in progress."
        : "We are preparing your shipment request.",
      done: stepIndex >= 1,
      active: stepIndex === 0 || stepIndex === 1
    },
    {
      label: "In Transit",
      detail: order.shipment?.courier
        ? `Moving with ${order.shipment.courier}.`
        : "Pickup and line-haul updates will appear here.",
      done: stepIndex >= 2,
      active: stepIndex === 2
    },
    {
      label: "Out For Delivery",
      detail: order.shipment?.estimated_delivery
        ? `Expected by ${formatShipmentDate(order.shipment.estimated_delivery)}.`
        : "Final-mile update will appear here.",
      done: stepIndex >= 3,
      active: stepIndex === 3
    },
    {
      label: "Delivered",
      detail: stepIndex >= 4 ? "Shipment delivered successfully." : "Delivery confirmation pending.",
      done: stepIndex >= 4,
      active: stepIndex === 4
    }
  ];
}

export function CustomerOrdersSection({
  orders,
  loading = false,
  error = "",
  title = "My Orders",
  emptyMessage = "No orders found for this account yet.",
  mode = "history",
}: CustomerOrdersSectionProps) {
  return (
    <section className="drawer-section">
      <div className="drawer-section-header">
        <h3>{title}</h3>
      </div>
      {loading ? <p className="muted">Loading your orders...</p> : null}
      {!loading && error ? <p className="status-message error">{error}</p> : null}
      {!loading && !error && orders.length === 0 ? (
        <p className="muted">{emptyMessage}</p>
      ) : null}
      {!loading && !error && orders.length > 0 ? (
        <div className="orders-list">
          {orders.map((order) => (
            <article key={order.order_number} className="order-card">
              <div className="order-header">
                <div>
                  <strong>{order.order_number}</strong>
                  <p className="order-subtitle">
                    {order.city}, {order.state} - {order.pincode}
                  </p>
                </div>
                <span>{formatOrderTotal(order.total_amount)}</span>
              </div>
              <p className="order-address">{order.delivery_address}</p>
              <div className="shipment-meta-grid">
                <div className="shipment-meta-card">
                  <span>Payment</span>
                  <strong>{order.payment_status}</strong>
                </div>
                <div className="shipment-meta-card">
                  <span>{mode === "tracking" ? "AWB" : "Order Status"}</span>
                  <strong>
                    {mode === "tracking"
                      ? order.shipment?.awb_number ?? "Will appear after courier booking"
                      : order.status}
                  </strong>
                </div>
                <div className="shipment-meta-card">
                  <span>{mode === "tracking" ? "Synced" : "Shipment"}</span>
                  <strong>
                    {mode === "tracking"
                      ? formatShipmentDateTime(order.shipment?.last_synced_at)
                      : order.shipment?.status ?? (order.payment_status === "paid" ? "Preparing shipment" : "Pending")}
                  </strong>
                </div>
              </div>
              {mode === "tracking" ? (
                <>
                  <div className={`shipment-banner shipment-banner-${getShipmentTone(order)}`}>
                    <div>
                      <strong>
                        {order.shipment?.status ?? (order.payment_status === "paid" ? "Preparing shipment" : "Payment pending")}
                      </strong>
                      <p>
                        {order.shipment?.estimated_delivery
                          ? `Estimated delivery: ${formatShipmentDate(order.shipment.estimated_delivery)}`
                          : order.shipment?.message
                            ? order.shipment.message
                            : order.shipment?.error
                              ? order.shipment.error
                              : "Real-time courier events will appear here once assigned."}
                      </p>
                    </div>
                    <span className="shipment-badge">
                      {order.shipment?.courier ?? order.shipment?.provider ?? "Lagads Care"}
                    </span>
                  </div>
                  <div className="shipment-timeline">
                    {getShipmentTimeline(order).map((step) => (
                      <div
                        key={step.label}
                        className={`shipment-step ${step.done ? "done" : ""} ${step.active ? "active" : ""}`}
                      >
                        <div className="shipment-step-dot" />
                        <div>
                          <strong>{step.label}</strong>
                          <p>{step.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  {order.shipment?.history?.length ? (
                    <div className="shipment-history">
                      {order.shipment.history.map((event, index) => (
                        <div key={`${order.order_number}-${event.status}-${index}`} className="shipment-history-row">
                          <div>
                            <strong>{event.status}</strong>
                            <p>{event.location ?? "Location update pending"}</p>
                          </div>
                          <span>{formatShipmentDateTime(event.timestamp)}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="order-subtitle">
                      Courier scan events will start showing here right after the shipment is picked up.
                    </p>
                  )}
                </>
              ) : (
                <p className="order-subtitle">
                  {order.shipment?.status
                    ? `Shipment status: ${order.shipment.status}`
                    : order.payment_status === "paid"
                      ? "Shipment preparation is in progress."
                      : "Payment confirmation is pending."}
                </p>
              )}
              <div className="metric-list">
                {order.items.map((item) => (
                  <div key={`${order.order_number}-${item.flavour}-${item.variant_label}`}>
                    {item.product_name.toLowerCase().includes(item.flavour.toLowerCase())
                      ? item.product_name
                      : `${item.product_name} - ${item.flavour}`}{" "}
                    - {item.variant_label} x {item.quantity}
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
