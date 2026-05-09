import logo from "../assets/company-logo.png";
import { Icon } from "./Icon";

type HeaderProps = {
  onMenuClick: () => void;
  onAccountClick: () => void;
  onCartClick: () => void;
  cartCount: number;
};

export function Header({
  onMenuClick,
  onAccountClick,
  onCartClick,
  cartCount
}: HeaderProps) {
  return (
    <header className="topbar">
      <button className="icon-button" onClick={onMenuClick} aria-label="Open menu">
        <Icon name="menu" />
      </button>

      <div className="brand-lockup">
        <img src={logo} alt="Lagads Nutrition logo" className="brand-logo" />
        <div>
          <p className="eyebrow">Lagads Nutrition</p>
          <h1>Lagads Nutrition</h1>
        </div>
      </div>

      <div className="topbar-actions">
        <button className="icon-button" onClick={onAccountClick} aria-label="Account">
          <Icon name="account" />
        </button>
        <button className="icon-button cart-button" onClick={onCartClick} aria-label="Cart">
          <Icon name="cart" />
          {cartCount > 0 ? <span className="cart-badge">{cartCount}</span> : null}
        </button>
      </div>
    </header>
  );
}
