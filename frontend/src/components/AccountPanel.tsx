import { useState } from "react";
import { buildAuthUser, useAuth } from "../context/AuthContext";
import { fetchCurrentUser, login, register } from "../services/auth";
import {
  createAdminProduct,
  deleteAdminProduct,
  fetchAdminHero,
  fetchAdminMetrics,
  fetchAdminProducts,
  resolveImageUrl,
  type AdminMetrics,
  type HeroPayload,
  updateAdminProduct,
  updateAdminHero,
  uploadAdminImage
} from "../services/admin";
import { fetchMyOrders, type CustomerOrder } from "../services/orders";
import type { HeroConfig } from "../types/hero";
import type { AdminProduct } from "../types/admin";
import { Icon } from "./Icon";

type AccountPanelProps = {
  open: boolean;
  onClose: () => void;
  onCatalogChange?: () => Promise<void> | void;
  onHeroChange?: () => Promise<void> | void;
};

type View = "menu" | "login" | "register" | "admin" | "orders";

type ProductFormState = {
  slug: string;
  name: string;
  flavour: string;
  description: string;
  image_urls: string[];
  category: string;
  variants: Array<{
    weight_label: string;
    mrp: string;
    selling_price: string;
    stock_quantity: string;
  }>;
};

type HeroFormState = {
  eyebrow_text: string;
  headline: string;
  body_text: string;
  cta_label: string;
  cta_link: string;
  offer_text: string;
  badge_title: string;
  badge_subtitle: string;
  image_urls: string[];
};

const emptyProductForm = (): ProductFormState => ({
  slug: "",
  name: "Peanut Butter",
  flavour: "",
  description: "",
  image_urls: ["", "", ""],
  category: "Peanut Butter",
  variants: [
    { weight_label: "1kg", mrp: "", selling_price: "", stock_quantity: "100" },
    { weight_label: "500g", mrp: "", selling_price: "", stock_quantity: "100" }
  ]
});

const emptyHeroForm = (): HeroFormState => ({
  eyebrow_text: "",
  headline: "",
  body_text: "",
  cta_label: "Shop Now",
  cta_link: "#products",
  offer_text: "",
  badge_title: "",
  badge_subtitle: "",
  image_urls: ["", "", ""]
});

function productToForm(product: AdminProduct): ProductFormState {
  return {
    slug: product.slug,
    name: product.name,
    flavour: product.flavour,
    description: product.description,
    image_urls: Array.from({ length: 3 }, (_, index) => product.images[index]?.image_url ?? ""),
    category: product.category,
    variants: product.variants.map((variant) => ({
      weight_label: variant.weight_label,
      mrp: String(variant.mrp),
      selling_price: String(variant.selling_price),
      stock_quantity: String(variant.stock_quantity)
    }))
  };
}

function buildProductPayload(form: ProductFormState) {
  return {
    slug: form.slug,
    name: form.name,
    flavour: form.flavour,
    description: form.description,
    image_url: form.image_urls.find((item) => item.trim()) || null,
    image_urls: form.image_urls.filter((item) => item.trim()).slice(0, 3),
    category: form.category,
    variants: form.variants.map((variant) => ({
      weight_label: variant.weight_label,
      mrp: Number(variant.mrp),
      selling_price: Number(variant.selling_price),
      stock_quantity: Number(variant.stock_quantity)
    }))
  };
}

function heroToForm(hero: HeroConfig): HeroFormState {
  return {
    eyebrow_text: hero.eyebrow_text,
    headline: hero.headline,
    body_text: hero.body_text,
    cta_label: hero.cta_label,
    cta_link: hero.cta_link,
    offer_text: hero.offer_text,
    badge_title: hero.badge_title,
    badge_subtitle: hero.badge_subtitle,
    image_urls: Array.from({ length: 3 }, (_, index) => hero.images[index]?.image_url ?? "")
  };
}

function buildHeroPayload(form: HeroFormState): HeroPayload {
  return {
    eyebrow_text: form.eyebrow_text,
    headline: form.headline,
    body_text: form.body_text,
    cta_label: form.cta_label,
    cta_link: form.cta_link,
    offer_text: form.offer_text,
    badge_title: form.badge_title,
    badge_subtitle: form.badge_subtitle,
    image_urls: form.image_urls.filter((item) => item.trim()).slice(0, 3)
  };
}

export function AccountPanel({ open, onClose, onCatalogChange, onHeroChange }: AccountPanelProps) {
  const { user, loginUser, logoutUser } = useAuth();
  const [view, setView] = useState<View>("menu");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [heroForm, setHeroForm] = useState<HeroFormState>(emptyHeroForm());
  const [editingProductId, setEditingProductId] = useState<number | null>(null);
  const [productForm, setProductForm] = useState<ProductFormState>(emptyProductForm());
  const [uploadingImage, setUploadingImage] = useState(false);

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerPhone, setRegisterPhone] = useState("");

  const resetFeedback = () => {
    setMessage("");
    setError("");
  };

  const goToView = (nextView: View) => {
    resetFeedback();
    if (nextView !== "admin") {
      setMetrics(null);
    }
    setView(nextView);
  };

  const handleLogin = async () => {
    resetFeedback();
    setLoading(true);

    try {
      const response = await login({
        email: loginEmail,
        password: loginPassword
      });
      localStorage.setItem("lagads-user-token", response.access_token);
      const currentUser = await fetchCurrentUser(response.access_token);
      loginUser(buildAuthUser(currentUser.email, currentUser.full_name, currentUser.is_admin));
      if (currentUser.is_admin) {
        localStorage.setItem("lagads-admin-token", response.access_token);
        const [dashboardMetrics, catalog, hero] = await Promise.all([
          fetchAdminMetrics(response.access_token),
          fetchAdminProducts(response.access_token),
          fetchAdminHero(response.access_token)
        ]);
        setProducts(catalog);
        setHeroForm(heroToForm(hero));
        setMetrics(dashboardMetrics);
        setEditingProductId(null);
        setProductForm(emptyProductForm());
        setView("admin");
        setMessage("Admin login successful. Dashboard loaded.");
      } else {
        setMessage("Login successful. Your customer session is ready.");
      }
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    resetFeedback();
    setLoading(true);

    try {
      const response = await register({
        full_name: registerName,
        email: registerEmail,
        password: registerPassword,
        phone_number: registerPhone || undefined
      });
      localStorage.setItem("lagads-user-token", response.access_token);
      const currentUser = await fetchCurrentUser(response.access_token);
      loginUser(buildAuthUser(currentUser.email, currentUser.full_name, currentUser.is_admin));
      setMessage("Registration successful. You are now logged in.");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdminDashboard = async () => {
    resetFeedback();
    const token = localStorage.getItem("lagads-admin-token") || localStorage.getItem("lagads-user-token");
    if (!token || !user?.isAdmin) {
      setError("Please log in with an admin account first.");
      return;
    }

    setLoading(true);

    try {
      const [dashboardMetrics, catalog, hero] = await Promise.all([
        fetchAdminMetrics(token),
        fetchAdminProducts(token),
        fetchAdminHero(token)
      ]);
      setProducts(catalog);
      setHeroForm(heroToForm(hero));
      setMetrics(dashboardMetrics);
      setEditingProductId(null);
      setProductForm(emptyProductForm());
      setView("admin");
      setMessage("Admin dashboard loaded.");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Unable to load admin dashboard.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenOrders = async () => {
    resetFeedback();
    const token = localStorage.getItem("lagads-user-token") || localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Please log in first to view your orders.");
      return;
    }

    setLoading(true);
    try {
      const nextOrders = await fetchMyOrders(token);
      setOrders(nextOrders);
      setView("orders");
    } catch (orderError) {
      setError(orderError instanceof Error ? orderError.message : "Unable to load orders.");
    } finally {
      setLoading(false);
    }
  };

  const refreshAdminCatalog = async (token: string) => {
    const [dashboardMetrics, catalog] = await Promise.all([
      fetchAdminMetrics(token),
      fetchAdminProducts(token)
    ]);
    setMetrics(dashboardMetrics);
    setProducts(catalog);
  };

  const handleEditProduct = (product: AdminProduct) => {
    resetFeedback();
    setEditingProductId(product.id);
    setProductForm(productToForm(product));
  };

  const handleCreateNewProduct = () => {
    resetFeedback();
    setEditingProductId(null);
    setProductForm(emptyProductForm());
  };

  const handleProductFieldChange = (
    key: keyof Omit<ProductFormState, "variants">,
    value: string
  ) => {
    setProductForm((current) => ({ ...current, [key]: value }));
  };

  const handleVariantChange = (
    index: number,
    key: keyof ProductFormState["variants"][number],
    value: string
  ) => {
    setProductForm((current) => ({
      ...current,
      variants: current.variants.map((variant, variantIndex) =>
        variantIndex === index ? { ...variant, [key]: value } : variant
      )
    }));
  };

  const handleImageUrlChange = (index: number, value: string) => {
    setProductForm((current) => ({
      ...current,
      image_urls: current.image_urls.map((imageUrl, imageIndex) =>
      imageIndex === index ? value : imageUrl
      )
    }));
  };

  const handleHeroFieldChange = (key: keyof Omit<HeroFormState, "image_urls">, value: string) => {
    setHeroForm((current) => ({ ...current, [key]: value }));
  };

  const handleHeroImageUrlChange = (index: number, value: string) => {
    setHeroForm((current) => ({
      ...current,
      image_urls: current.image_urls.map((imageUrl, imageIndex) =>
        imageIndex === index ? value : imageUrl
      )
    }));
  };

  const handleSaveProduct = async () => {
    resetFeedback();
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    setLoading(true);
    try {
      const payload = buildProductPayload(productForm);
      if (editingProductId) {
        await updateAdminProduct(token, editingProductId, payload);
        setMessage("Product updated successfully.");
      } else {
        await createAdminProduct(token, payload);
        setMessage("Product created successfully.");
      }

      await refreshAdminCatalog(token);
      await onCatalogChange?.();
      setEditingProductId(null);
      setProductForm(emptyProductForm());
    } catch (productError) {
      setError(productError instanceof Error ? productError.message : "Unable to save product.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async (productId: number) => {
    resetFeedback();
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    setLoading(true);
    try {
      await deleteAdminProduct(token, productId);
      await refreshAdminCatalog(token);
      await onCatalogChange?.();
      if (editingProductId === productId) {
        setEditingProductId(null);
        setProductForm(emptyProductForm());
      }
      setMessage("Product deleted successfully.");
    } catch (productError) {
      setError(productError instanceof Error ? productError.message : "Unable to delete product.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveHero = async () => {
    resetFeedback();
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    setLoading(true);
    try {
      const updatedHero = await updateAdminHero(token, buildHeroPayload(heroForm));
      setHeroForm(heroToForm(updatedHero));
      await onHeroChange?.();
      setMessage("Homepage hero updated successfully.");
    } catch (heroError) {
      setError(heroError instanceof Error ? heroError.message : "Unable to update hero settings.");
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (slotIndex: number, file: File | null) => {
    if (!file) {
      return;
    }
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    resetFeedback();
    setUploadingImage(true);
    try {
      const imageUrl = await uploadAdminImage(token, file);
      setProductForm((current) => ({
        ...current,
        image_urls: current.image_urls.map((existingUrl, imageIndex) =>
          imageIndex === slotIndex ? imageUrl : existingUrl
        )
      }));
      setMessage(`Image ${slotIndex + 1} uploaded successfully.`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Unable to upload image.");
    } finally {
      setUploadingImage(false);
    }
  };

  const handleHeroImageUpload = async (slotIndex: number, file: File | null) => {
    if (!file) {
      return;
    }
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    resetFeedback();
    setUploadingImage(true);
    try {
      const imageUrl = await uploadAdminImage(token, file);
      setHeroForm((current) => ({
        ...current,
        image_urls: current.image_urls.map((existingUrl, imageIndex) =>
          imageIndex === slotIndex ? imageUrl : existingUrl
        )
      }));
      setMessage(`Hero image ${slotIndex + 1} uploaded successfully.`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Unable to upload hero image.");
    } finally {
      setUploadingImage(false);
    }
  };

  return (
    <aside className={`panel ${open ? "open" : ""} ${view === "admin" ? "panel-admin" : ""}`}>
      <div className="drawer-header">
        <h2>Account</h2>
        <button className="icon-button" onClick={onClose} aria-label="Close account panel">
          <Icon name="close" />
        </button>
      </div>
      {user ? (
        <div className="signed-in-banner">
          <div>
            <strong>{user.fullName}</strong>
            <p>{user.email}</p>
            <p>{user.isAdmin ? "Admin session active" : "Customer session active"}</p>
          </div>
          <button
            className="text-button"
            onClick={() => {
              logoutUser();
              setMetrics(null);
              setView("menu");
              resetFeedback();
            }}
          >
            Logout
          </button>
        </div>
      ) : null}
      {view === "menu" ? (
        <>
          <div className="panel-actions">
            {user ? (
              <button className="pill pill-primary" onClick={onClose}>
                Continue Shopping
              </button>
            ) : (
              <>
                <button className="pill pill-primary" onClick={() => goToView("login")}>
                  Login
                </button>
                <button className="pill" onClick={() => goToView("register")}>
                  Register
                </button>
              </>
            )}
          </div>
          <div className="panel-links">
            {user?.isAdmin ? (
              <button className="text-link-button" onClick={handleOpenAdminDashboard} disabled={loading}>
                Admin Dashboard
              </button>
            ) : null}
            <a href="#orders" onClick={onClose}>
              Saved Checkout Details
            </a>
            <button className="text-link-button" onClick={handleOpenOrders} disabled={loading}>
              Your Orders
            </button>
            <a href="#customer-feedback" onClick={onClose}>
              Customer Feedback
            </a>
          </div>
        </>
      ) : null}

      {view === "login" ? (
        <div className="auth-shell">
          <button className="text-button" onClick={() => goToView("menu")}>
            Back
          </button>
          <div className="field">
            <span>Email</span>
            <input value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)} />
          </div>
          <div className="field">
            <span>Password</span>
            <input
              type="password"
              value={loginPassword}
              onChange={(event) => setLoginPassword(event.target.value)}
            />
          </div>
          <button className="pill pill-primary" onClick={handleLogin} disabled={loading}>
            {loading ? "Please wait..." : "Login"}
          </button>
        </div>
      ) : null}

      {view === "register" ? (
        <div className="auth-shell">
          <button className="text-button" onClick={() => goToView("menu")}>
            Back
          </button>
          <div className="field">
            <span>Full Name</span>
            <input
              value={registerName}
              onChange={(event) => setRegisterName(event.target.value)}
            />
          </div>
          <div className="field">
            <span>Email</span>
            <input
              value={registerEmail}
              onChange={(event) => setRegisterEmail(event.target.value)}
            />
          </div>
          <div className="field">
            <span>Password</span>
            <input
              type="password"
              value={registerPassword}
              onChange={(event) => setRegisterPassword(event.target.value)}
            />
          </div>
          <div className="field">
            <span>Phone Number</span>
            <input
              value={registerPhone}
              onChange={(event) => setRegisterPhone(event.target.value)}
            />
          </div>
          <button className="pill pill-primary" onClick={handleRegister} disabled={loading}>
            {loading ? "Please wait..." : "Create Account"}
          </button>
        </div>
      ) : null}

      {view === "admin" ? (
        <div className="auth-shell admin-workspace">
          <button className="text-button" onClick={() => goToView("menu")}>
            Back
          </button>
          {metrics ? (
            <>
              <div className="admin-metrics">
                <h3>Sales Snapshot</h3>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <span>Total Orders</span>
                    <strong>{metrics.total_orders}</strong>
                  </div>
                  <div className="metric-card">
                    <span>Total Revenue</span>
                    <strong>Rs. {metrics.total_revenue}</strong>
                  </div>
                  <div className="metric-card">
                    <span>Top Products</span>
                    <div className="metric-list">
                      {metrics.top_products.length === 0
                        ? "No orders yet."
                        : metrics.top_products.map(([name, qty]) => `${name}: ${qty}`).join(", ")}
                    </div>
                  </div>
                </div>
              </div>

              <div className="admin-layout">
                <section className="admin-section">
                  <div className="admin-section-header">
                    <h3>Homepage Hero</h3>
                    <span>Control the main banner text, badge copy, CTA, and up to 3 hero images.</span>
                  </div>

                  <div className="field">
                    <span>Eyebrow Text</span>
                    <input
                      value={heroForm.eyebrow_text}
                      onChange={(event) => handleHeroFieldChange("eyebrow_text", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Headline</span>
                    <textarea
                      rows={3}
                      value={heroForm.headline}
                      onChange={(event) => handleHeroFieldChange("headline", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Body Text</span>
                    <textarea
                      rows={5}
                      value={heroForm.body_text}
                      onChange={(event) => handleHeroFieldChange("body_text", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>CTA Label</span>
                    <input
                      value={heroForm.cta_label}
                      onChange={(event) => handleHeroFieldChange("cta_label", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>CTA Link</span>
                    <input
                      value={heroForm.cta_link}
                      onChange={(event) => handleHeroFieldChange("cta_link", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Offer Text</span>
                    <input
                      value={heroForm.offer_text}
                      onChange={(event) => handleHeroFieldChange("offer_text", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Badge Title</span>
                    <input
                      value={heroForm.badge_title}
                      onChange={(event) => handleHeroFieldChange("badge_title", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Badge Subtitle</span>
                    <input
                      value={heroForm.badge_subtitle}
                      onChange={(event) => handleHeroFieldChange("badge_subtitle", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Hero Images</span>
                    <p className="muted">Upload up to 3 hero images. They rotate automatically on the homepage.</p>
                    <div className="admin-image-grid">
                      {heroForm.image_urls.map((imageUrl, index) => (
                        <div key={`hero-image-${index}`} className="admin-image-slot">
                          <strong>Hero Image {index + 1}</strong>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(event) =>
                              handleHeroImageUpload(index, event.target.files?.[0] ?? null)
                            }
                          />
                          <input
                            type="text"
                            value={imageUrl}
                            placeholder="Uploaded hero image URL will appear here"
                            onChange={(event) => handleHeroImageUrlChange(index, event.target.value)}
                          />
                          {uploadingImage ? <span className="muted">Uploading image...</span> : null}
                          {resolveImageUrl(imageUrl) ? (
                            <img
                              src={resolveImageUrl(imageUrl) ?? ""}
                              alt={`Hero preview ${index + 1}`}
                              className="admin-upload-preview"
                            />
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="admin-inline-actions">
                    <button className="pill pill-primary" onClick={handleSaveHero} disabled={loading}>
                      Save Hero
                    </button>
                  </div>
                </section>

                <section className="admin-section">
                  <div className="admin-section-header">
                    <h3>Product Catalog</h3>
                    <button className="pill" onClick={handleCreateNewProduct}>
                      Add New Product
                    </button>
                  </div>
                  <div className="admin-product-grid">
                    {products.map((product) => (
                      <article key={product.id} className="admin-product-card">
                        {resolveImageUrl(product.image_url) ? (
                          <img
                            src={resolveImageUrl(product.image_url) ?? ""}
                            alt={product.flavour}
                            className="admin-product-image"
                          />
                        ) : (
                          <div className="admin-product-placeholder">No image</div>
                        )}
                        <div className="admin-product-body">
                          <strong>{product.flavour}</strong>
                          <span>{product.slug}</span>
                          <span>{product.variants.map((variant) => `${variant.weight_label}: Rs. ${variant.selling_price}`).join(" | ")}</span>
                          <div className="admin-inline-actions">
                            <button className="pill" onClick={() => handleEditProduct(product)}>
                              Edit
                            </button>
                            <button
                              className="pill pill-muted"
                              onClick={() => handleDeleteProduct(product.id)}
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="admin-section">
                  <div className="admin-section-header">
                    <h3>{editingProductId ? "Edit Product" : "Create Product"}</h3>
                    <span>{editingProductId ? "Update pricing, description, variants, and image." : "Add a new product to the storefront."}</span>
                  </div>
                  <div className="field">
                    <span>Slug</span>
                    <input
                      value={productForm.slug}
                      onChange={(event) => handleProductFieldChange("slug", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Name</span>
                    <input
                      value={productForm.name}
                      onChange={(event) => handleProductFieldChange("name", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Flavour</span>
                    <input
                      value={productForm.flavour}
                      onChange={(event) => handleProductFieldChange("flavour", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Description</span>
                    <textarea
                      rows={6}
                      value={productForm.description}
                      onChange={(event) => handleProductFieldChange("description", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Category</span>
                    <input
                      value={productForm.category}
                      onChange={(event) => handleProductFieldChange("category", event.target.value)}
                    />
                  </div>
                  <div className="field">
                    <span>Product Images</span>
                    <p className="muted">Upload up to 3 images. The first image becomes the main storefront image.</p>
                    <div className="admin-image-grid">
                      {productForm.image_urls.map((imageUrl, index) => (
                        <div key={`product-image-${index}`} className="admin-image-slot">
                          <strong>Image {index + 1}</strong>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(event) =>
                              handleImageUpload(index, event.target.files?.[0] ?? null)
                            }
                          />
                          <input
                            type="text"
                            value={imageUrl}
                            placeholder="Uploaded image URL will appear here"
                            onChange={(event) => handleImageUrlChange(index, event.target.value)}
                          />
                          {uploadingImage ? <span className="muted">Uploading image...</span> : null}
                          {resolveImageUrl(imageUrl) ? (
                            <img
                              src={resolveImageUrl(imageUrl) ?? ""}
                              alt={`Uploaded preview ${index + 1}`}
                              className="admin-upload-preview"
                            />
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="variant-editor">
                    {productForm.variants.map((variant, index) => (
                      <div key={`${variant.weight_label}-${index}`} className="variant-row">
                        <div className="field">
                          <span>Weight</span>
                          <input
                            value={variant.weight_label}
                            onChange={(event) =>
                              handleVariantChange(index, "weight_label", event.target.value)
                            }
                          />
                        </div>
                        <div className="field">
                          <span>MRP</span>
                          <input
                            value={variant.mrp}
                            onChange={(event) =>
                              handleVariantChange(index, "mrp", event.target.value)
                            }
                          />
                        </div>
                        <div className="field">
                          <span>Selling Price</span>
                          <input
                            value={variant.selling_price}
                            onChange={(event) =>
                              handleVariantChange(index, "selling_price", event.target.value)
                            }
                          />
                        </div>
                        <div className="field">
                          <span>Stock</span>
                          <input
                            value={variant.stock_quantity}
                            onChange={(event) =>
                              handleVariantChange(index, "stock_quantity", event.target.value)
                            }
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="admin-inline-actions">
                    <button className="pill pill-primary" onClick={handleSaveProduct} disabled={loading}>
                      {editingProductId ? "Update Product" : "Create Product"}
                    </button>
                    <button className="pill" onClick={handleCreateNewProduct}>
                      Reset Form
                    </button>
                  </div>
                </section>
              </div>
            </>
          ) : null}
        </div>
      ) : null}

      {view === "orders" ? (
        <div className="auth-shell">
          <button className="text-button" onClick={() => goToView("menu")}>
            Back
          </button>
          <h3>Your Orders</h3>
          {orders.length === 0 ? (
            <p className="muted">No orders found for this account yet.</p>
          ) : (
            <div className="orders-list">
              {orders.map((order) => (
                <article key={order.order_number} className="order-card">
                  <div className="order-header">
                    <strong>{order.order_number}</strong>
                    <span>Rs. {order.total_amount}</span>
                  </div>
                  <p>
                    {order.status} | {order.payment_status}
                  </p>
                  <p>{order.delivery_address}</p>
                  <div className="metric-list">
                    {order.items.map((item) => (
                      <div key={`${order.order_number}-${item.flavour}-${item.variant_label}`}>
                        {item.product_name} - {item.flavour} - {item.variant_label} x {item.quantity}
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      ) : null}

      {message ? <p className="status-message success">{message}</p> : null}
      {error ? <p className="status-message error">{error}</p> : null}
    </aside>
  );
}
