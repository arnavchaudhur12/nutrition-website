import { useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { createPaymentOrder, notifyPaymentFailure, previewCoupon, verifyPayment } from "../services/payments";
import type { Product } from "../types";

type CheckoutSectionProps = {
  products: Product[];
};

const razorpayKeyId = import.meta.env.VITE_RAZORPAY_KEY_ID ?? "";

function getSessionToken(): string {
  return localStorage.getItem("lagads-user-token") || localStorage.getItem("lagads-admin-token") || "";
}

const initialFormState = {
  customerName: "",
  deliveryAddress: "",
  phoneNumber: "",
  email: "",
  alternatePhoneNumber: "",
  comments: "",
  couponCode: ""
};

function formatRupees(amount: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(amount);
}

export function CheckoutSection({ products }: CheckoutSectionProps) {
  const { user } = useAuth();
  const { items, clearCart } = useCart();
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [form, setForm] = useState(initialFormState);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState<"success" | "error" | "">("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const paymentFlowLock = useRef(false);
  const [couponDiscountPercent, setCouponDiscountPercent] = useState(0);
  const [couponStatus, setCouponStatus] = useState("");

  const enrichedCart = useMemo(
    () =>
      items
        .map((item) => {
          const product = products.find((candidate) => candidate.id === item.productId);
          const variant = product?.variants.find((candidate) => candidate.id === item.variantId);
          return product && variant ? { ...item, product, variant } : null;
        })
        .filter((item): item is NonNullable<typeof item> => Boolean(item)),
    [items, products]
  );

  const totalAmount = enrichedCart.reduce(
    (total, item) => total + item.variant.sellingPrice * item.quantity,
    0
  );
  const itemTotal = enrichedCart.reduce((total, item) => total + item.variant.mrp * item.quantity, 0);
  const itemCount = enrichedCart.reduce((total, item) => total + item.quantity, 0);
  const productCount = enrichedCart.length;
  const discountedTotal = Math.max(
    1,
    Math.round((totalAmount * ((100 - couponDiscountPercent) / 100)) * 100) / 100
  );
  const discountAmount = Math.max(0, Math.round((totalAmount - discountedTotal) * 100) / 100);
  const premiumSavings = Math.max(0, Math.round((itemTotal - totalAmount) * 100) / 100);
  const totalSavings = Math.round((premiumSavings + discountAmount) * 100) / 100;

  const updateField = (field: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const showStatus = (type: "success" | "error", message: string) => {
    setStatusType(type);
    setStatusMessage(message);
  };

  const validateCheckout = () => {
    if (!razorpayKeyId) {
      return "Razorpay public key is not configured.";
    }
    if (!window.Razorpay) {
      return "Razorpay checkout script is still loading. Please try again.";
    }
    if (enrichedCart.length === 0) {
      return "Add at least one product to the cart before payment.";
    }
    if (!form.customerName || !form.deliveryAddress || !form.phoneNumber || !form.email) {
      return "Please fill name, delivery address, phone number, and email.";
    }
    if (totalAmount < 1) {
      return "Minimum payment amount is Rs. 1.";
    }
    return "";
  };

  const handlePayment = async () => {
    if (paymentFlowLock.current) {
      return;
    }
    paymentFlowLock.current = true;

    const token = getSessionToken();
    const validationError = validateCheckout();
    if (validationError) {
      showStatus("error", validationError);
      paymentFlowLock.current = false;
      return;
    }

    setIsSubmitting(true);
    setStatusMessage("");
    setStatusType("");

    try {
      const RazorpayCheckout = window.Razorpay;
      if (!RazorpayCheckout) {
        throw new Error("Razorpay checkout script is still loading. Please try again.");
      }

      const payload = {
        currency: "INR",
        customer_name: form.customerName,
        email: form.email,
        phone_number: form.phoneNumber,
        alternate_phone_number: form.alternatePhoneNumber || undefined,
        delivery_address: form.deliveryAddress,
        comments: form.comments || undefined,
        coupon_code: form.couponCode.trim() || undefined,
        items: enrichedCart.map((item) => ({
          product_slug: item.product.id,
          variant_id: Number(item.variant.id),
          quantity: item.quantity
        }))
      };

      const activeToken = token || undefined;
      const paymentOrder = await createPaymentOrder(payload, activeToken);

      const razorpay = new RazorpayCheckout({
        key: razorpayKeyId,
        amount: paymentOrder.amount,
        currency: paymentOrder.currency,
        name: "Lagad's Nutrition",
        description: "Nutrition products order",
        order_id: paymentOrder.order_id,
        prefill: {
          name: form.customerName,
          email: form.email,
          contact: form.phoneNumber
        },
        notes: {
          order_number: paymentOrder.app_order_number ?? undefined
        },
        theme: {
          color: "#ff7a00"
        },
        modal: {
          ondismiss: () => {
            setIsSubmitting(false);
            paymentFlowLock.current = false;
            void notifyPaymentFailure(
              {
                razorpay_order_id: paymentOrder.order_id,
                reason: "cancelled",
                description: "Customer closed the payment window before completing payment."
              },
              activeToken
            ).catch(() => undefined);
            showStatus("error", "Payment was cancelled before completion.");
          }
        },
        handler: async (response) => {
          try {
            const result = await verifyPayment(response, activeToken);
            setIsSubmitting(false);
            paymentFlowLock.current = false;
            clearCart();
            setCouponDiscountPercent(0);
            setCouponStatus("");
            setForm(initialFormState);
            setDetailsOpen(false);
            window.alert(
              "Thank you for your purchase from Lagads Nutrition! Please stay on this website for a couple of seconds and do not refresh."
            );
            showStatus(
              "success",
              result.order_number
                ? `Payment verified. Order ${result.order_number} is confirmed.`
                : "Payment verified successfully."
            );
          } catch (error) {
            setIsSubmitting(false);
            paymentFlowLock.current = false;
            showStatus(
              "error",
              error instanceof Error ? error.message : "Payment verification failed."
            );
          }
        }
      });

      razorpay.on("payment.failed", (response) => {
        setIsSubmitting(false);
        paymentFlowLock.current = false;
        void notifyPaymentFailure(
          {
            razorpay_order_id: response.error?.metadata?.order_id ?? paymentOrder.order_id,
            razorpay_payment_id: response.error?.metadata?.payment_id,
            reason: response.error?.reason,
            description: response.error?.description
          },
          activeToken
        ).catch(() => undefined);
        showStatus(
          "error",
          response.error?.description ?? response.error?.reason ?? "Payment failed. Please try again."
        );
      });

      razorpay.open();
    } catch (error) {
      setIsSubmitting(false);
      paymentFlowLock.current = false;
      showStatus("error", error instanceof Error ? error.message : "Unable to start payment.");
    }
  };

  useEffect(() => {
    const token = getSessionToken();
    const couponCode = form.couponCode.trim().toUpperCase();
    if (!couponCode) {
      setCouponDiscountPercent(0);
      setCouponStatus("");
      return;
    }
    if (couponCode.length !== 6 || !/^[A-Z0-9]{6}$/.test(couponCode)) {
      setCouponDiscountPercent(0);
      setCouponStatus("Coupon must be exactly 6 letters or numbers.");
      return;
    }
    let cancelled = false;
    void previewCoupon(couponCode, token || undefined)
      .then((result) => {
        if (cancelled) return;
        setCouponDiscountPercent(result.discount_percent);
        const previewDiscountAmount =
          Math.round((totalAmount * (result.discount_percent / 100)) * 100) / 100;
        const previewFinalAmount = Math.max(1, Math.round((totalAmount - previewDiscountAmount) * 100) / 100);
        setCouponStatus(
          `${result.discount_percent}% OFF applied: ${formatRupees(totalAmount)} -> ${formatRupees(previewFinalAmount)}`
        );
      })
      .catch(() => {
        if (cancelled) return;
        setCouponDiscountPercent(0);
        setCouponStatus("Invalid coupon code.");
      });

    return () => {
      cancelled = true;
    };
  }, [form.couponCode]);

  return (
    <section className="checkout-shell" id="checkout">
      <div>
        <p className="eyebrow">Checkout workflow</p>
        <h2>Review your order, then open customer details when you're ready</h2>
        <p>
          The customer detail form stays closed until the shopper clicks for it. Order summary,
          product breakup, savings, and final payable amount are visible before the payment gateway opens.
        </p>
        {user ? (
          <p className="muted">
            Logged-in users also get order history in their account after successful payment.
          </p>
        ) : null}
      </div>

      <div className="checkout-form">
        <div className="checkout-order-card">
          <div className="checkout-order-header">
            <div>
              <span className="eyebrow">Order Summary</span>
              <h3>
                {itemCount} Item{itemCount === 1 ? "" : "s"}
              </h3>
            </div>
            <button
              type="button"
              className="pill"
              onClick={() => setDetailsOpen((current) => !current)}
            >
              {detailsOpen ? "Hide Customer Details" : "Customer Details"}
            </button>
          </div>

          <div className="checkout-product-list">
            {enrichedCart.length === 0 ? (
              <p className="muted">Add products to the cart to see the payment breakup.</p>
            ) : (
              enrichedCart.map((item) => (
                <article
                  key={`${item.productId}-${item.variantId}`}
                  className="checkout-product-row"
                >
                  <div>
                    <strong>{item.product.flavour}</strong>
                    <p>
                      {item.variant.weight} x {item.quantity}
                    </p>
                  </div>
                  <strong>{formatRupees(item.variant.sellingPrice * item.quantity)}</strong>
                </article>
              ))
            )}
          </div>

          <div className="checkout-summary-grid">
            <div className="checkout-summary-row">
              <span>Item Total</span>
              <strong>{formatRupees(itemTotal)}</strong>
            </div>
            <div className="checkout-summary-row">
              <span>Delivery Fee</span>
              <strong>FREE</strong>
            </div>
            <div className="checkout-summary-row">
              <span>Product Savings</span>
              <strong>-{formatRupees(premiumSavings)}</strong>
            </div>
            <div className="checkout-summary-row">
              <span>Coupon Discount</span>
              <strong>-{formatRupees(discountAmount)}</strong>
            </div>
            <div className="checkout-summary-row">
              <span>Product Count</span>
              <strong>{productCount}</strong>
            </div>
            <div className="checkout-summary-row checkout-summary-row-total">
              <span>To Pay</span>
              <strong>{formatRupees(discountedTotal)}</strong>
            </div>
          </div>

          {totalSavings > 0 ? (
            <p className="muted">Total savings before payment: {formatRupees(totalSavings)}</p>
          ) : null}
        </div>

        {detailsOpen ? (
          <form className="checkout-details-card">
            <label className="field">
              <span>Full Name</span>
              <input
                placeholder="Enter full name"
                value={form.customerName}
                onChange={(event) => updateField("customerName", event.target.value)}
              />
            </label>
            <label className="field">
              <span>Delivery Address</span>
              <textarea
                placeholder="House number, street, city, state, pin code"
                rows={4}
                value={form.deliveryAddress}
                onChange={(event) => updateField("deliveryAddress", event.target.value)}
              />
            </label>
            <label className="field">
              <span>Phone Number</span>
              <input
                placeholder="Primary mobile number"
                value={form.phoneNumber}
                onChange={(event) => updateField("phoneNumber", event.target.value)}
              />
            </label>
            <label className="field">
              <span>Email Address</span>
              <input
                type="email"
                placeholder="your@email.com"
                value={form.email}
                onChange={(event) => updateField("email", event.target.value)}
              />
            </label>
            <label className="field">
              <span>Alternative Phone Number</span>
              <input
                placeholder="Optional alternate mobile number"
                value={form.alternatePhoneNumber}
                onChange={(event) => updateField("alternatePhoneNumber", event.target.value)}
              />
            </label>
            <label className="field">
              <span>Coupon Code (Optional)</span>
              <input
                placeholder="Enter 6-character coupon"
                value={form.couponCode}
                onChange={(event) => updateField("couponCode", event.target.value.toUpperCase())}
                maxLength={6}
              />
            </label>
            <label className="field">
              <span>Comments or Special Request</span>
              <textarea
                placeholder="Any delivery notes or preferences"
                rows={3}
                value={form.comments}
                onChange={(event) => updateField("comments", event.target.value)}
              />
            </label>
            {couponStatus ? (
              <p className={`status-message ${couponDiscountPercent > 0 ? "success" : "error"}`}>
                {couponStatus}
              </p>
            ) : null}
            <button
              type="button"
              className="pill pill-primary"
              onClick={handlePayment}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Opening Payment..." : "Continue to Payment Gateway"}
            </button>
            {statusMessage ? <p className={`status-message ${statusType}`}>{statusMessage}</p> : null}
          </form>
        ) : (
          <div className="checkout-collapsed-note">
            <p>Customer details stay hidden until the shopper opens the form.</p>
          </div>
        )}
      </div>
    </section>
  );
}
