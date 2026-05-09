import { useState } from "react";
import { Header } from "./components/Header";
import { SideDrawer } from "./components/SideDrawer";
import { AccountPanel } from "./components/AccountPanel";
import { CartDrawer } from "./components/CartDrawer";
import { HeroCarousel } from "./components/HeroCarousel";
import { ProductCard } from "./components/ProductCard";
import { CheckoutSection } from "./components/CheckoutSection";
import { InfoSections } from "./components/InfoSections";
import { useAuth } from "./context/AuthContext";
import { products } from "./data/products";
import { useCart } from "./context/CartContext";

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);
  const { itemCount } = useCart();
  const { user } = useAuth();

  return (
    <div className="app-shell">
      <SideDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />
      <AccountPanel open={accountOpen} onClose={() => setAccountOpen(false)} />
      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} />

      <Header
        onMenuClick={() => setMenuOpen(true)}
        onAccountClick={() => setAccountOpen(true)}
        onCartClick={() => setCartOpen(true)}
        cartCount={itemCount}
        profileInitial={user?.initial ?? null}
      />

      <main>
        <HeroCarousel />

        <section className="section-heading" id="products">
          <div>
            <p className="eyebrow">Peanut Butter</p>
            <h2>Slide into the catalog, choose flavour, and price updates dynamically</h2>
          </div>
          <p>
            This first version keeps the product catalog focused and premium while already
            preparing the data model for future product expansion, admin management, and
            analytics.
          </p>
        </section>

        <section className="product-grid">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </section>

        <CheckoutSection />
        <InfoSections />
      </main>
    </div>
  );
}
