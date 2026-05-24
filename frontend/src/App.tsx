import { useEffect, useState } from "react";
import { Header } from "./components/Header";
import { SideDrawer } from "./components/SideDrawer";
import { AccountPanel } from "./components/AccountPanel";
import { CartDrawer } from "./components/CartDrawer";
import { HeroCarousel } from "./components/HeroCarousel";
import { ProductCard } from "./components/ProductCard";
import { CheckoutSection } from "./components/CheckoutSection";
import { InfoSections } from "./components/InfoSections";
import { useAuth } from "./context/AuthContext";
import { useCart } from "./context/CartContext";
import { fetchHeroConfig } from "./services/hero";
import { fetchStorefrontProducts } from "./services/products";
import type { HeroConfig } from "./types/hero";
import type { Product } from "./types";

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [hero, setHero] = useState<HeroConfig | null>(null);
  const [productsLoading, setProductsLoading] = useState(true);
  const [productsError, setProductsError] = useState("");
  const { itemCount } = useCart();
  const { user } = useAuth();

  const loadProducts = async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setProductsLoading(true);
    }

    try {
      const catalog = await fetchStorefrontProducts();
      setProducts(catalog);
      setProductsError("");
    } catch (error) {
      if (!options?.silent || products.length === 0) {
        setProductsError(error instanceof Error ? error.message : "Unable to load products.");
      }
    } finally {
      if (!options?.silent) {
        setProductsLoading(false);
      }
    }
  };

  const loadHero = async () => {
    try {
      const nextHero = await fetchHeroConfig();
      setHero(nextHero);
    } catch (error) {
      if (!hero) {
        setProductsError(error instanceof Error ? error.message : "Unable to load hero settings.");
      }
    }
  };

  useEffect(() => {
    void loadProducts();
    void loadHero();
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void loadProducts({ silent: true });
      void loadHero();
    }, 15000);

    return () => window.clearInterval(timer);
  }, [products.length]);

  return (
    <div className="app-shell">
      <SideDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />
      <AccountPanel
        open={accountOpen}
        onClose={() => setAccountOpen(false)}
        onCatalogChange={loadProducts}
        onHeroChange={loadHero}
      />
      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} products={products} />

      <Header
        onMenuClick={() => setMenuOpen(true)}
        onAccountClick={() => setAccountOpen(true)}
        onCartClick={() => setCartOpen(true)}
        cartCount={itemCount}
        profileInitial={user?.initial ?? null}
      />

      <main>
        <HeroCarousel hero={hero} />

        <section className="section-heading" id="products">
          <div>
            <p className="eyebrow">Peanut Butter</p>
            <h2>Flavour You’ll Crave Again & Again</h2>
          </div>
          <p>Smooth texture, rich taste, and nutrition that fits your lifestyle.</p>
        </section>

        <section className="product-grid">
          {productsLoading ? <p className="catalog-message">Loading product catalog...</p> : null}
          {!productsLoading && productsError ? (
            <p className="catalog-message">{productsError}</p>
          ) : null}
          {!productsLoading && !productsError && products.length === 0 ? (
            <p className="catalog-message">No products are live right now. Add one from the admin dashboard.</p>
          ) : null}
          {!productsLoading && !productsError
            ? products.map((product) => <ProductCard key={product.id} product={product} />)
            : null}
        </section>

        <CheckoutSection products={products} />
        <InfoSections />
      </main>
    </div>
  );
}
