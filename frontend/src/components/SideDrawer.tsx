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
    </aside>
  );
}
