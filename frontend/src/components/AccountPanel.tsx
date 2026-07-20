import { useMemo, useState } from "react";
import { buildAuthUser, useAuth } from "../context/AuthContext";
import { fetchCurrentUser, login, register, resetPassword } from "../services/auth";
import {
  createAdminCoupon,
  createAdminProduct,
  deleteAdminCoupon,
  deleteAdminProduct,
  downloadInvoiceStatement,
  fetchAdminCouponOrders,
  fetchAdminCustomerPortfolio,
  fetchAdminCoupons,
  fetchAdminHero,
  fetchAdminMetrics,
  fetchAdminProducts,
  resolveImageUrl,
  type AdminDashboardPeriod,
  type AdminCustomerPortfolio,
  type AdminCouponOrderSummary,
  type AdminMetrics,
  type CouponCode,
  type HeroPayload,
  updateAdminProduct,
  updateAdminHero,
  uploadAdminImage
} from "../services/admin";
import type { HeroConfig } from "../types/hero";
import type { AdminProduct } from "../types/admin";
import { Icon } from "./Icon";

type AccountPanelProps = {
  open: boolean;
  onClose: () => void;
  onCatalogChange?: () => Promise<void> | void;
  onHeroChange?: () => Promise<void> | void;
};

type View = "menu" | "login" | "register" | "reset" | "admin";

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

type PortfolioFilters = {
  created_at: string;
  customer_name: string;
  delivery_address: string;
  payment_mode: string;
  amount_count: string;
  products: string;
  product_quantity: string;
  product_count: string;
  phone_number: string;
  email: string;
};

const emptyProductForm = (): ProductFormState => ({
  slug: "",
  name: "",
  flavour: "",
  description: "",
  image_urls: ["", "", "", "", ""],
  category: "",
  variants: [
    { weight_label: "1kg", mrp: "", selling_price: "", stock_quantity: "100" },
    { weight_label: "500g", mrp: "", selling_price: "", stock_quantity: "100" }
  ]
});

const emptyHeroForm = (): HeroFormState => ({
  eyebrow_text: "",
  headline: "",
  body_text: "",
  cta_label: "",
  cta_link: "",
  offer_text: "",
  badge_title: "",
  badge_subtitle: "",
  image_urls: ["", "", "", "", "", ""]
});

const emptyPortfolioFilters = (): PortfolioFilters => ({
  created_at: "",
  customer_name: "",
  delivery_address: "",
  payment_mode: "",
  amount_count: "",
  products: "",
  product_quantity: "",
  product_count: "",
  phone_number: "",
  email: ""
});

function productToForm(product: AdminProduct): ProductFormState {
  return {
    slug: product.slug,
    name: product.name,
    flavour: product.flavour,
    description: product.description,
    image_urls: Array.from({ length: 5 }, (_, index) => product.images[index]?.image_url ?? ""),
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
    image_urls: form.image_urls.filter((item) => item.trim()).slice(0, 5),
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
  const imageUrls = Array.from({ length: 6 }, () => "");
  for (const image of hero.images) {
    if (image.sort_order >= 0 && image.sort_order < imageUrls.length) {
      imageUrls[image.sort_order] = image.image_url;
    }
  }

  return {
    eyebrow_text: hero.eyebrow_text,
    headline: hero.headline,
    body_text: hero.body_text,
    cta_label: hero.cta_label,
    cta_link: hero.cta_link,
    offer_text: hero.offer_text,
    badge_title: hero.badge_title,
    badge_subtitle: hero.badge_subtitle,
    image_urls: imageUrls
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
    image_urls: form.image_urls.map((item) => item.trim()).slice(0, 6)
  };
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(amount);
}

function formatDiscountPercent(mrp: string, sellingPrice: string): string {
  const mrpValue = Number(mrp);
  const sellingValue = Number(sellingPrice);
  if (!Number.isFinite(mrpValue) || !Number.isFinite(sellingValue) || mrpValue <= 0 || sellingValue >= mrpValue) {
    return "0%";
  }
  return `${Math.round(((mrpValue - sellingValue) / mrpValue) * 100)}%`;
}

function formatPortfolioDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function normalizeMetrics(metrics: AdminMetrics): AdminMetrics {
  return {
    total_actual_sales_count: metrics.total_actual_sales_count ?? 0,
    total_actual_revenue: metrics.total_actual_revenue ?? 0,
    total_products_sold: metrics.total_products_sold ?? 0,
    product_performance: Array.isArray(metrics.product_performance)
      ? metrics.product_performance
      : [],
    note: metrics.note ?? ""
  };
}

function formatDateInput(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function AccountPanel({ open, onClose, onCatalogChange, onHeroChange }: AccountPanelProps) {
  const { user, loginUser, logoutUser } = useAuth();
  const [view, setView] = useState<View>("menu");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<AdminDashboardPeriod>("all_time");
  const [customerPortfolio, setCustomerPortfolio] = useState<AdminCustomerPortfolio[]>([]);
  const [couponOrders, setCouponOrders] = useState<AdminCouponOrderSummary[]>([]);
  const [portfolioFilters, setPortfolioFilters] = useState<PortfolioFilters>(
    emptyPortfolioFilters()
  );
  const [coupons, setCoupons] = useState<CouponCode[]>([]);
  const [newCouponCode, setNewCouponCode] = useState("");
  const [newCouponDiscount, setNewCouponDiscount] = useState("10");
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [heroForm, setHeroForm] = useState<HeroFormState>(emptyHeroForm());
  const [editingProductId, setEditingProductId] = useState<number | null>(null);
  const [productForm, setProductForm] = useState<ProductFormState>(emptyProductForm());
  const [uploadingImage, setUploadingImage] = useState(false);
  const [invoiceStartDate, setInvoiceStartDate] = useState(() =>
    formatDateInput(new Date(Date.now() - (29 * 24 * 60 * 60 * 1000)))
  );
  const [invoiceEndDate, setInvoiceEndDate] = useState(() => formatDateInput(new Date()));

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [registerPhone, setRegisterPhone] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetPasswordValue, setResetPasswordValue] = useState("");
  const [showResetPassword, setShowResetPassword] = useState(false);

  const filteredCustomerPortfolio = useMemo(() => {
    const normalize = (value: string) => value.trim().toLowerCase();

    return customerPortfolio.filter((row) => {
      const matchesText = (source: string, filterValue: string) =>
        source.toLowerCase().includes(normalize(filterValue));

      if (portfolioFilters.created_at && !matchesText(formatPortfolioDate(row.created_at), portfolioFilters.created_at)) {
        return false;
      }
      if (portfolioFilters.customer_name && !matchesText(row.customer_name, portfolioFilters.customer_name)) {
        return false;
      }
      if (portfolioFilters.delivery_address && !matchesText(row.delivery_address, portfolioFilters.delivery_address)) {
        return false;
      }
      if (portfolioFilters.payment_mode && !matchesText(row.payment_mode, portfolioFilters.payment_mode)) {
        return false;
      }
      if (portfolioFilters.amount_count && !String(row.amount_count).includes(portfolioFilters.amount_count.trim())) {
        return false;
      }
      if (portfolioFilters.products && !matchesText(row.products, portfolioFilters.products)) {
        return false;
      }
      if (portfolioFilters.product_quantity && !String(row.product_quantity).includes(portfolioFilters.product_quantity.trim())) {
        return false;
      }
      if (portfolioFilters.product_count && !String(row.product_count).includes(portfolioFilters.product_count.trim())) {
        return false;
      }
      if (portfolioFilters.phone_number && !matchesText(row.phone_number, portfolioFilters.phone_number)) {
        return false;
      }
      if (portfolioFilters.email && !matchesText(row.email, portfolioFilters.email)) {
        return false;
      }
      return true;
    });
  }, [customerPortfolio, portfolioFilters]);

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
      const period: AdminDashboardPeriod = "all_time";
      if (currentUser.is_admin) {
        localStorage.setItem("lagads-admin-token", response.access_token);
        const [dashboardMetrics, portfolio, couponSummary, catalog, hero, couponList] = await Promise.all([
          fetchAdminMetrics(response.access_token, period),
          fetchAdminCustomerPortfolio(response.access_token, period),
          fetchAdminCouponOrders(response.access_token, period),
          fetchAdminProducts(response.access_token),
          fetchAdminHero(response.access_token),
          fetchAdminCoupons(response.access_token)
        ]);
        setSelectedPeriod(period);
        setMetrics(normalizeMetrics(dashboardMetrics));
        setCustomerPortfolio(portfolio);
        setCouponOrders(couponSummary);
        setProducts(catalog);
        setHeroForm(heroToForm(hero));
        setCoupons(couponList);
        setEditingProductId(null);
        setProductForm(emptyProductForm());
        setPortfolioFilters(emptyPortfolioFilters());
        setView("admin");
        setMessage("Admin login successful. Dashboard loaded.");
      } else {
        setView("menu");
        setMessage("Login successful. Your customer session is ready.");
        onClose();
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

  const handleResetPassword = async () => {
    resetFeedback();
    setLoading(true);
    try {
      await resetPassword({
        email: resetEmail,
        new_password: resetPasswordValue
      });
      setMessage("Password reset successful. Please login with your new password.");
      setView("login");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Password reset failed.");
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
      const [dashboardMetrics, portfolio, couponSummary, catalog, hero, couponList] = await Promise.all([
        fetchAdminMetrics(token, selectedPeriod),
        fetchAdminCustomerPortfolio(token, selectedPeriod),
        fetchAdminCouponOrders(token, selectedPeriod),
        fetchAdminProducts(token),
        fetchAdminHero(token),
        fetchAdminCoupons(token)
      ]);
      setCustomerPortfolio(portfolio);
      setCouponOrders(couponSummary);
      setProducts(catalog);
      setHeroForm(heroToForm(hero));
      setMetrics(normalizeMetrics(dashboardMetrics));
      setCoupons(couponList);
      setEditingProductId(null);
      setProductForm(emptyProductForm());
      setPortfolioFilters(emptyPortfolioFilters());
      setView("admin");
      setMessage("Admin dashboard loaded.");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Unable to load admin dashboard.");
    } finally {
      setLoading(false);
    }
  };

  const refreshAdminCatalog = async (token: string) => {
    const [dashboardMetrics, portfolio, couponSummary, catalog, couponList] = await Promise.all([
      fetchAdminMetrics(token, selectedPeriod),
      fetchAdminCustomerPortfolio(token, selectedPeriod),
      fetchAdminCouponOrders(token, selectedPeriod),
      fetchAdminProducts(token),
      fetchAdminCoupons(token)
    ]);
    setMetrics(normalizeMetrics(dashboardMetrics));
    setCustomerPortfolio(portfolio);
    setCouponOrders(couponSummary);
    setProducts(catalog);
    setCoupons(couponList);
  };

  const handlePortfolioFilterChange = (key: keyof PortfolioFilters, value: string) => {
    setPortfolioFilters((current) => ({ ...current, [key]: value }));
  };

  const handlePeriodChange = async (period: AdminDashboardPeriod) => {
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    resetFeedback();
    setLoading(true);
    try {
      const [dashboardMetrics, portfolio, couponSummary] = await Promise.all([
        fetchAdminMetrics(token, period),
        fetchAdminCustomerPortfolio(token, period),
        fetchAdminCouponOrders(token, period)
      ]);
      setSelectedPeriod(period);
      setMetrics(normalizeMetrics(dashboardMetrics));
      setCustomerPortfolio(portfolio);
      setCouponOrders(couponSummary);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to update date filter.");
    } finally {
      setLoading(false);
    }
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

  const handleRemoveHeroImage = (index: number) => {
    setHeroForm((current) => ({
      ...current,
      image_urls: current.image_urls.map((imageUrl, imageIndex) =>
        imageIndex === index ? "" : imageUrl
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

  const handleCreateCoupon = async () => {
    resetFeedback();
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    setLoading(true);
    try {
      await createAdminCoupon(token, {
        code: newCouponCode.trim().toUpperCase(),
        discount_percent: Number(newCouponDiscount)
      });
      await refreshAdminCatalog(token);
      setNewCouponCode("");
      setNewCouponDiscount("10");
      setMessage("Coupon code created successfully.");
    } catch (couponError) {
      setError(couponError instanceof Error ? couponError.message : "Unable to create coupon code.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCoupon = async (code: string) => {
    resetFeedback();
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }

    setLoading(true);
    try {
      await deleteAdminCoupon(token, code);
      await refreshAdminCatalog(token);
      setMessage(`Coupon ${code} deleted successfully.`);
    } catch (couponError) {
      setError(couponError instanceof Error ? couponError.message : "Unable to delete coupon code.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadInvoiceStatement = async () => {
    resetFeedback();
    const token = localStorage.getItem("lagads-admin-token");
    if (!token) {
      setError("Admin token missing. Please log in again.");
      return;
    }
    if (!invoiceStartDate || !invoiceEndDate) {
      setError("Please select both start and end dates.");
      return;
    }
    if (invoiceEndDate < invoiceStartDate) {
      setError("End date must be on or after start date.");
      return;
    }

    setLoading(true);
    try {
      const { blob, filename } = await downloadInvoiceStatement(
        token,
        invoiceStartDate,
        invoiceEndDate
      );
      const downloadUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = downloadUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(downloadUrl);
      setMessage(`Invoice statement downloaded for ${invoiceStartDate} to ${invoiceEndDate}.`);
    } catch (downloadError) {
      setError(
        downloadError instanceof Error
          ? downloadError.message
          : "Unable to download invoice statement."
      );
    } finally {
      setLoading(false);
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
            <div className="password-field">
              <input
                type={showLoginPassword ? "text" : "password"}
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
              />
              <button
                type="button"
                className="text-button"
                onClick={() => setShowLoginPassword((current) => !current)}
              >
                {showLoginPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>
          <button className="pill pill-primary" onClick={handleLogin} disabled={loading}>
            {loading ? "Please wait..." : "Login"}
          </button>
          <button className="text-button" onClick={() => goToView("reset")}>
            Forgot Password?
          </button>
        </div>
      ) : null}

      {view === "reset" ? (
        <div className="auth-shell">
          <button className="text-button" onClick={() => goToView("login")}>
            Back to Login
          </button>
          <div className="field">
            <span>Email</span>
            <input value={resetEmail} onChange={(event) => setResetEmail(event.target.value)} />
          </div>
          <div className="field">
            <span>New Password</span>
            <div className="password-field">
              <input
                type={showResetPassword ? "text" : "password"}
                value={resetPasswordValue}
                onChange={(event) => setResetPasswordValue(event.target.value)}
              />
              <button
                type="button"
                className="text-button"
                onClick={() => setShowResetPassword((current) => !current)}
              >
                {showResetPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>
          <button className="pill pill-primary" onClick={handleResetPassword} disabled={loading}>
            {loading ? "Please wait..." : "Reset Password"}
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
            <div className="password-field">
              <input
                type={showRegisterPassword ? "text" : "password"}
                value={registerPassword}
                onChange={(event) => setRegisterPassword(event.target.value)}
              />
              <button
                type="button"
                className="text-button"
                onClick={() => setShowRegisterPassword((current) => !current)}
              >
                {showRegisterPassword ? "Hide" : "Show"}
              </button>
            </div>
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
              <div className="admin-tabs">
                <a href="#admin-sales" className="pill">Sales</a>
                <a href="#admin-portfolio" className="pill">Customer Portfolio</a>
                <a href="#admin-coupons" className="pill">Coupons</a>
                <a href="#admin-coupon-orders" className="pill">Coupon Orders</a>
                <a href="#admin-hero" className="pill">Hero Images</a>
                <a href="#admin-products" className="pill">Products</a>
              </div>
              <div className="admin-period-filter">
                <span>Date Range</span>
                <select
                  value={selectedPeriod}
                  onChange={(event) => handlePeriodChange(event.target.value as AdminDashboardPeriod)}
                >
                  <option value="last_7_days">Last 7 Days</option>
                  <option value="last_30_days">Last 30 Days</option>
                  <option value="last_90_days">Last 90 Days</option>
                  <option value="all_time">All Time</option>
                </select>
              </div>
              <div className="admin-metrics">
                <h3>Sales Snapshot</h3>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <span>Total Actual Sales Count</span>
                    <strong>{metrics.total_actual_sales_count}</strong>
                  </div>
                  <div className="metric-card">
                    <span>Total Actual Revenue</span>
                    <strong>{formatCurrency(metrics.total_actual_revenue)}</strong>
                  </div>
                  <div className="metric-card">
                    <span>Total Product Quantity Sold</span>
                    <strong>{metrics.total_products_sold}</strong>
                  </div>
                </div>
                <p className="muted">{metrics.note}</p>
              </div>

              <div className="admin-layout">
                <section className="admin-section admin-section-wide" id="admin-sales">
                  <div className="admin-section-header">
                    <h3>Product Performance</h3>
                    <span>Product-wise quantity and revenue excluding cancelled and failed orders.</span>
                  </div>
                  <div className="admin-table-shell">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>Total Product Wise Count</th>
                          <th>Total Product Wise Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.product_performance.length === 0 ? (
                          <tr>
                            <td colSpan={3} className="admin-table-empty">No successful sales yet.</td>
                          </tr>
                        ) : (
                          metrics.product_performance.map((product) => (
                            <tr key={product.product_name}>
                              <td>{product.product_name}</td>
                              <td>{product.quantity_sold}</td>
                              <td>{formatCurrency(product.total_amount)}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="admin-section admin-section-wide" id="admin-portfolio">
                  <div className="admin-section-header">
                    <h3>Customer Portfolio</h3>
                    <span>Historical customer journey in tabular format with column-level filters.</span>
                  </div>
                  <div className="admin-inline-actions" style={{ marginBottom: "1rem", alignItems: "flex-end", flexWrap: "wrap" }}>
                    <label className="field" style={{ margin: 0 }}>
                      <span>Invoice Start Date</span>
                      <input
                        type="date"
                        value={invoiceStartDate}
                        onChange={(event) => setInvoiceStartDate(event.target.value)}
                      />
                    </label>
                    <label className="field" style={{ margin: 0 }}>
                      <span>Invoice End Date</span>
                      <input
                        type="date"
                        value={invoiceEndDate}
                        onChange={(event) => setInvoiceEndDate(event.target.value)}
                      />
                    </label>
                    <button
                      className="pill pill-primary"
                      onClick={handleDownloadInvoiceStatement}
                      disabled={loading}
                    >
                      {loading ? "Preparing PDF..." : "Download Invoice Statement"}
                    </button>
                  </div>
                  <div className="admin-table-shell">
                    <table className="admin-table admin-table-portfolio">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Person Name</th>
                          <th>Person Address</th>
                          <th>Payment Mode</th>
                          <th>Only Success</th>
                          <th>Amount Count</th>
                          <th>Products</th>
                          <th>Product Quantity</th>
                          <th>Product Count</th>
                          <th>Phone Number</th>
                          <th>Email Address</th>
                        </tr>
                        <tr className="admin-table-filters">
                          <th><input value={portfolioFilters.created_at} onChange={(event) => handlePortfolioFilterChange("created_at", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.customer_name} onChange={(event) => handlePortfolioFilterChange("customer_name", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.delivery_address} onChange={(event) => handlePortfolioFilterChange("delivery_address", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.payment_mode} onChange={(event) => handlePortfolioFilterChange("payment_mode", event.target.value)} placeholder="Filter" /></th>
                          <th><input value="Success" readOnly /></th>
                          <th><input value={portfolioFilters.amount_count} onChange={(event) => handlePortfolioFilterChange("amount_count", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.products} onChange={(event) => handlePortfolioFilterChange("products", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.product_quantity} onChange={(event) => handlePortfolioFilterChange("product_quantity", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.product_count} onChange={(event) => handlePortfolioFilterChange("product_count", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.phone_number} onChange={(event) => handlePortfolioFilterChange("phone_number", event.target.value)} placeholder="Filter" /></th>
                          <th><input value={portfolioFilters.email} onChange={(event) => handlePortfolioFilterChange("email", event.target.value)} placeholder="Filter" /></th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredCustomerPortfolio.length === 0 ? (
                          <tr>
                            <td colSpan={11} className="admin-table-empty">No matching customer journeys found.</td>
                          </tr>
                        ) : (
                          filteredCustomerPortfolio.map((entry) => (
                            <tr key={entry.order_number}>
                              <td>{formatPortfolioDate(entry.created_at)}</td>
                              <td>{entry.customer_name}</td>
                              <td>{entry.delivery_address}</td>
                              <td>{entry.payment_mode}</td>
                              <td>Success</td>
                              <td>{formatCurrency(entry.amount_count)}</td>
                              <td>{entry.products}</td>
                              <td>{entry.product_quantity}</td>
                              <td>{entry.product_count}</td>
                              <td>{entry.phone_number}</td>
                              <td>{entry.email}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="admin-section" id="admin-coupons">
                  <div className="admin-section-header">
                    <h3>Coupon Codes</h3>
                    <span>Create 6-character alphanumeric coupons with percentage discount.</span>
                  </div>
                  <div className="field">
                    <span>Coupon Code</span>
                    <input
                      value={newCouponCode}
                      maxLength={6}
                      placeholder="e.g. SAVE10"
                      onChange={(event) => setNewCouponCode(event.target.value.toUpperCase())}
                    />
                  </div>
                  <div className="field">
                    <span>Discount Percent</span>
                    <input
                      type="number"
                      min={1}
                      max={90}
                      value={newCouponDiscount}
                      onChange={(event) => setNewCouponDiscount(event.target.value)}
                    />
                  </div>
                  <div className="admin-inline-actions">
                    <button className="pill pill-primary" onClick={handleCreateCoupon} disabled={loading}>
                      Add Coupon
                    </button>
                  </div>
                  <div className="orders-list">
                    {coupons.length === 0 ? (
                      <p className="muted">No coupons created yet.</p>
                    ) : (
                      coupons.map((coupon) => (
                        <article key={coupon.id} className="order-card">
                          <div className="order-header">
                            <strong>{coupon.code}</strong>
                            <span>{coupon.discount_percent}% OFF</span>
                          </div>
                          <button
                            className="pill pill-muted"
                            onClick={() => handleDeleteCoupon(coupon.code)}
                          >
                            Delete
                          </button>
                        </article>
                      ))
                    )}
                  </div>
                </section>

                <section className="admin-section" id="admin-coupon-orders">
                  <div className="admin-section-header">
                    <h3>Coupon Wise Orders</h3>
                    <span>Successful orders grouped against each coupon for the selected date range.</span>
                  </div>
                  <div className="admin-table-shell">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Coupon Code</th>
                          <th>Orders Count</th>
                          <th>Total Revenue</th>
                          <th>Total Products Sold</th>
                          <th>Order Numbers</th>
                        </tr>
                      </thead>
                      <tbody>
                        {couponOrders.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="admin-table-empty">No successful coupon-based orders found.</td>
                          </tr>
                        ) : (
                          couponOrders.map((entry) => (
                            <tr key={entry.coupon_code}>
                              <td>{entry.coupon_code}</td>
                              <td>{entry.orders_count}</td>
                              <td>{formatCurrency(entry.total_revenue)}</td>
                              <td>{entry.total_products_sold}</td>
                              <td>{entry.order_numbers}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="admin-section" id="admin-hero">
                  <div className="admin-section-header">
                    <h3>Website And Mobile Font Images</h3>
                    <span>Manage slideshow images only.</span>
                  </div>
                  <div className="field">
                    <span>Hero Images</span>
                    <p className="muted">Upload 3 website slideshow images and 3 mobile slideshow images. The live homepage rotates them every 3 seconds.</p>
                    <div className="admin-image-grid">
                      {heroForm.image_urls.map((imageUrl, index) => (
                        <div key={`hero-image-${index}`} className="admin-image-slot">
                          <strong>
                            {index <= 2
                              ? `Website Font Image ${index + 1}`
                              : `Mobile Font Image ${index - 2}`}
                          </strong>
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
                          <button
                            type="button"
                            className="pill pill-muted"
                            onClick={() => handleRemoveHeroImage(index)}
                            disabled={!imageUrl.trim()}
                          >
                            Remove Image
                          </button>
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

                <section className="admin-section" id="admin-products">
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
                          <span>{product.name}</span>
                          <span>{product.slug}</span>
                          <span>
                            {product.variants
                              .map(
                                (variant) =>
                                  `${variant.weight_label}: Rs. ${variant.selling_price} (${variant.stock_quantity} in stock)`
                              )
                              .join(" | ")}
                          </span>
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
                    <p className="muted">Upload up to 5 images. The first image becomes the main storefront image.</p>
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
                        <div className="field">
                          <span>Discount</span>
                          <input
                            value={formatDiscountPercent(variant.mrp, variant.selling_price)}
                            readOnly
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

      {message ? <p className="status-message success">{message}</p> : null}
      {error ? <p className="status-message error">{error}</p> : null}
    </aside>
  );
}
