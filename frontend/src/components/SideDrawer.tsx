import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchMyOrders, type CustomerOrder } from "../services/orders";
import { CustomerOrdersSection } from "./CustomerOrdersSection";
import { Icon } from "./Icon";

type SideDrawerProps = {
  open: boolean;
  onClose: () => void;
};

const menuItems: Array<{ label: string; href: string }> = [
  { label: "Peanut Butter", href: "#products" },
  { label: "About Us", href: "#about-us" },
  { label: "Customer Feedback", href: "#customer-feedback" },
  { label: "Newsletter", href: "#newsletter" },
  { label: "Terms & Conditions", href: "#terms-conditions" }
];

export function SideDrawer({ open, onClose }: SideDrawerProps) {
  const { user } = useAuth();
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [ordersError, setOrdersError] = useState("");

  useEffect(() => {
    if (!open || !user) {
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
  }, [open, user]);

  return (
    <aside className={`drawer ${open ? "open" : ""}`}>
      <div className="drawer-header">
        <h2>Explore</h2>
        <button className="icon-button" onClick={onClose} aria-label="Close menu">
          <Icon name="close" />
        </button>
      </div>
      <nav className="drawer-nav">
        {menuItems.map((item) => (
          <a key={item.label} href={item.href} onClick={onClose}>
            {item.label}
          </a>
        ))}
      </nav>
      {user ? (
        <CustomerOrdersSection
          orders={orders}
          loading={ordersLoading}
          error={ordersError}
          title="My Orders"
        />
      ) : null}
    </aside>
  );
}
