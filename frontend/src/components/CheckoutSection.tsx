import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { createPaymentOrder, notifyPaymentFailure, previewCoupon, verifyPayment } from "../services/payments";
import type { Product } from "../types";

type CheckoutSectionProps = {
  products: Product[];
};

const razorpayKeyId = import.meta.env.VITE_RAZORPAY_KEY_ID ?? "";

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
  const { items } = useCart();
  const [form, setForm] = useState(initialFormState);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState<"success" | "error" | "">("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [couponDiscountPercent, setCouponDiscountPercent] = useState(0);
  const [couponStatus, setCouponStatus] = useState("");

  useEffect(() => {
    if (!user) {
      return;
    }

    setForm((current) => ({
      ...current,
      customerName: current.customerName || user.fullName,
      email: current.email || user.email
    }));
  }, [user]);

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
  const discountedTotal = Math.max(
    1,
    Math.round((totalAmount * ((100 - couponDiscountPercent) / 100)) * 100) / 100
  );

  const updateField = (field: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const showStatus = (type: "success" | "error", message: string) => {
    setStatusType(type);
    setStatusMessage(message);
  };

  const validateCheckout = () => {
    const token = localStorage.getItem("lagads-user-token");
    if (!user || !token) {
      return "Please log in before placing an order or making payment.";
    }
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
    const token = localStorage.getItem("lagads-user-token");
    const validationError = validateCheckout();
    if (validationError) {
      showStatus("error", validationError);
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

      const paymentOrder = await createPaymentOrder({
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
      }, token || "");

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
            void notifyPaymentFailure(
              {
                razorpay_order_id: paymentOrder.order_id,
                reason: "cancelled",
                description: "Customer closed the payment window before completing payment."
              },
              token || ""
            ).catch(() => undefined);
            showStatus("error", "Payment was cancelled before completion.");
          }
        },
        handler: async (response) => {
          try {
            const result = await verifyPayment(response, token || "");
            setIsSubmitting(false);
            showStatus(
              "success",
              result.order_number
                ? `Payment verified. Order ${result.order_number} is confirmed.`
                : "Payment verified successfully."
            );
          } catch (error) {
            setIsSubmitting(false);
            showStatus(
              "error",
              error instanceof Error ? error.message : "Payment verification failed."
            );
          }
        }
      });

      razorpay.on("payment.failed", (response) => {
        setIsSubmitting(false);
        void notifyPaymentFailure(
          {
            razorpay_order_id: response.error?.metadata?.order_id ?? paymentOrder.order_id,
            razorpay_payment_id: response.error?.metadata?.payment_id,
            reason: response.error?.reason,
            description: response.error?.description
          },
          token || ""
        ).catch(() => undefined);
        showStatus(
          "error",
          response.error?.description ?? response.error?.reason ?? "Payment failed. Please try again."
        );
      });

      razorpay.open();
    } catch (error) {
      setIsSubmitting(false);
      showStatus("error", error instanceof Error ? error.message : "Unable to start payment.");
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("lagads-user-token");
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
    if (!token) {
      setCouponDiscountPercent(0);
      setCouponStatus("Login first to validate coupon.");
      return;
    }

    let cancelled = false;
    void previewCoupon(couponCode, token)
      .then((result) => {
        if (cancelled) return;
        setCouponDiscountPercent(result.discount_percent);
        setCouponStatus(`${result.discount_percent}% discount applied.`);
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
        <h2>Login before payment, then confirm delivery details</h2>
        <p>
          Users add products to cart first, then log in or register, fill delivery details,
          review comments and continue to the payment gateway. Both the buyer and admin receive
          a confirmation email after successful payment.
        </p>
      </div>

      <form className="checkout-form">
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
        <div className="checkout-summary">
          <span>{couponDiscountPercent > 0 ? "Discounted Total" : "Cart Total"}</span>
          <strong>{formatRupees(couponDiscountPercent > 0 ? discountedTotal : totalAmount)}</strong>
        </div>
        {couponStatus ? <p className={`status-message ${couponDiscountPercent > 0 ? "success" : "error"}`}>{couponStatus}</p> : null}
        <button
          type="button"
          className="pill pill-primary"
          onClick={handlePayment}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Opening Payment..." : "Continue to Payment Gateway"}
        </button>
        {statusMessage ? (
          <p className={`status-message ${statusType}`}>{statusMessage}</p>
        ) : null}
      </form>
    </section>
  );
}
