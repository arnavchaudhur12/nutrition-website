import logo from "../assets/company-logo.PNG";
import { Icon } from "./Icon";

type HeaderProps = {
  onMenuClick: () => void;
  onAccountClick: () => void;
  onCartClick: () => void;
  cartCount: number;
  profileInitial?: string | null;
};

export function Header({
  onMenuClick,
  onAccountClick,
  onCartClick,
  cartCount,
  profileInitial
}: HeaderProps) {
  return (
    <header className="topbar">
      <button className="icon-button" onClick={onMenuClick} aria-label="Open menu">
        <Icon name="menu" />
      </button>

      <div className="brand-lockup">
        <img src={logo} alt="Lagad’s Nutrition logo" className="brand-logo" />
        <div>
          <h1>Lagad’s Nutrition</h1>
        </div>
      </div>

      <div className="topbar-actions">
        {profileInitial ? (
          <button className="icon-button" onClick={onAccountClick} aria-label="Account">
            <span className="profile-initial">{profileInitial}</span>
          </button>
        ) : (
          <button className="login-signup-button" onClick={onAccountClick} aria-label="Login or Sign Up">
            Login / Sign Up
          </button>
        )}
        <button className="icon-button cart-button" onClick={onCartClick} aria-label="Cart">
          <Icon name="cart" />
          {cartCount > 0 ? <span className="cart-badge">{cartCount}</span> : null}
        </button>
      </div>
    </header>
  );
}
