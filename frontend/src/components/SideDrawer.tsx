import { Icon } from "./Icon";

type SideDrawerProps = {
  open: boolean;
  onClose: () => void;
};

const menuItems = ["Peanut Butter", "About Us", "Customer Feedback", "Newsletter"];

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
          <a key={item} href={`#${item.toLowerCase().replace(/\s+/g, "-")}`} onClick={onClose}>
            {item}
          </a>
        ))}
      </nav>
    </aside>
  );
}

