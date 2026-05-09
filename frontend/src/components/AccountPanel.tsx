import { Icon } from "./Icon";

type AccountPanelProps = {
  open: boolean;
  onClose: () => void;
};

export function AccountPanel({ open, onClose }: AccountPanelProps) {
  return (
    <aside className={`panel ${open ? "open" : ""}`}>
      <div className="drawer-header">
        <h2>Account</h2>
        <button className="icon-button" onClick={onClose} aria-label="Close account panel">
          <Icon name="close" />
        </button>
      </div>
      <div className="panel-actions">
        <button className="pill pill-primary">Login</button>
        <button className="pill">Register</button>
        <button className="pill pill-muted">Admin</button>
      </div>
      <div className="panel-links">
        <a href="#orders">Your Orders</a>
        <a href="#checkout">Saved Checkout Details</a>
        <a href="#feedback">Customer Feedback</a>
      </div>
    </aside>
  );
}

