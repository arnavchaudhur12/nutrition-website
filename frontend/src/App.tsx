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
import {
  connectVisitor,
  disconnectVisitor,
  fetchActiveVisitors,
  sendVisitorHeartbeat
} from "./services/visitors";
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
  const [activeVisitors, setActiveVisitors] = useState<number | null>(null);
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

  useEffect(() => {
    let isMounted = true;
    let sessionId: string | null = null;

    const startTracking = async () => {
      try {
        const snapshot = await fetchActiveVisitors();
        if (isMounted) {
          setActiveVisitors(snapshot.active_visitors);
        }

        const session = await connectVisitor();
        sessionId = session.session_id;

        if (isMounted) {
          setActiveVisitors(session.active_visitors);
        }
      } catch (error) {
        if (isMounted) {
          setActiveVisitors(null);
          console.error(error);
        }
      }
    };

    void startTracking();

    const heartbeatTimer = window.setInterval(() => {
      if (!sessionId) {
        return;
      }

      void sendVisitorHeartbeat(sessionId)
        .then((session) => {
          if (isMounted) {
            setActiveVisitors(session.active_visitors);
          }
        })
        .catch((error) => {
          if (isMounted) {
            console.error(error);
          }
        });
    }, 15000);

    const handlePageHide = () => {
      if (sessionId) {
        void disconnectVisitor(sessionId);
      }
    };

    window.addEventListener("pagehide", handlePageHide);

    return () => {
      isMounted = false;
      window.clearInterval(heartbeatTimer);
      window.removeEventListener("pagehide", handlePageHide);
      if (sessionId) {
        void disconnectVisitor(sessionId);
      }
    };
  }, []);

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

      <footer className="visitor-counter" aria-live="polite">
        <span className="visitor-counter__label">Live visitors</span>
        <strong className="visitor-counter__value">
          {activeVisitors === null ? "..." : activeVisitors}
        </strong>
      </footer>
    </div>
  );
}
