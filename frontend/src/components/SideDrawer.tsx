import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchMyOrders, type CustomerOrder } from "../services/orders";
import { CustomerOrdersSection } from "./CustomerOrdersSection";
import { Icon } from "./Icon";

type SideDrawerProps = {
  open: boolean;
  onClose: () => void;
};

type DrawerView = "menu" | "orders-menu" | "my-orders" | "track-orders";

const menuItems: Array<{ label: string; href: string }> = [
  { label: "Peanut Butter", href: "#products" },
  { label: "About Us", href: "#about-us" },
  { label: "Customer Feedback", href: "#customer-feedback" },
  { label: "Newsletter", href: "#newsletter" },
  { label: "Terms & Conditions", href: "#terms-conditions" }
];

export function SideDrawer({ open, onClose }: SideDrawerProps) {
  const { user } = useAuth();
  const [view, setView] = useState<DrawerView>("menu");
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [ordersError, setOrdersError] = useState("");

  useEffect(() => {
    if (!open) {
      return;
    }

    if (!user || (view !== "my-orders" && view !== "track-orders")) {
      return;
    }

    const token = localStorage.getItem("lagads-user-token") || localStorage.getItem("lagads-admin-token");
    if (!token) {
      setOrders([]);
      setOrdersError("Please log in first to view your orders.");
      return;
    }

    let active = true;
    setOrdersLoading(true);
    setOrdersError("");

    void fetchMyOrders(token)
      .then((nextOrders) => {
        if (!active) {
          return;
        }
        setOrders(nextOrders);
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setOrdersError(error instanceof Error ? error.message : "Unable to load orders.");
      })
      .finally(() => {
        if (!active) {
          return;
        }
        setOrdersLoading(false);
      });

    return () => {
      active = false;
    };
  }, [open, user, view]);

  useEffect(() => {
    if (!open) {
      setView("menu");
    }
  }, [open]);

  const trackableOrders = orders.filter((order) =>
    Boolean(order.shipment?.order_id || order.shipment?.awb_number || order.shipment?.status || order.payment_status === "paid")
  );

  return (
    <aside className={`drawer ${open ? "open" : ""}`}>
      <div className="drawer-header">
        <h2>
          {view === "my-orders"
            ? "My Orders"
            : view === "track-orders"
              ? "Track Order"
              : view === "orders-menu"
                ? "Orders"
                : "Explore"}
        </h2>
        <button className="icon-button" onClick={onClose} aria-label="Close menu">
          <Icon name="close" />
        </button>
      </div>
      {view === "menu" ? (
        <>
          <nav className="drawer-nav">
            {menuItems.map((item) => (
              <a key={item.label} href={item.href} onClick={onClose}>
                {item.label}
              </a>
            ))}
            {user ? (
              <button type="button" className="text-link-button" onClick={() => setView("orders-menu")}>
                My Orders
              </button>
            ) : null}
          </nav>
        </>
      ) : null}
      {view === "orders-menu" ? (
        <div className="drawer-orders-shell">
          <button type="button" className="text-button" onClick={() => setView("menu")}>
            Back
          </button>
          <div className="drawer-orders-grid">
            <button type="button" className="drawer-order-tile" onClick={() => setView("my-orders")}>
              <span className="drawer-order-tile-icon">
                <Icon name="box" />
              </span>
              <span>My Orders</span>
            </button>
            <button type="button" className="drawer-order-tile" onClick={() => setView("track-orders")}>
              <span className="drawer-order-tile-icon">
                <Icon name="truck" />
              </span>
              <span>Track Order</span>
            </button>
          </div>
        </div>
      ) : null}
      {view === "my-orders" ? (
        <div className="drawer-orders-shell">
          <button type="button" className="text-button" onClick={() => setView("orders-menu")}>
            Back
          </button>
          <CustomerOrdersSection
            orders={orders}
            loading={ordersLoading}
            error={ordersError}
            title="My Orders"
            mode="history"
          />
        </div>
      ) : null}
      {view === "track-orders" ? (
        <div className="drawer-orders-shell">
          <button type="button" className="text-button" onClick={() => setView("orders-menu")}>
            Back
          </button>
          <CustomerOrdersSection
            orders={trackableOrders}
            loading={ordersLoading}
            error={ordersError}
            title="Track Order"
            emptyMessage="No trackable shipments are available yet."
            mode="tracking"
          />
        </div>
      ) : null}
    </aside>
  );
}
