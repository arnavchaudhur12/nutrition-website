import { useEffect, useMemo, useRef, useState } from "react";
import { getCitiesOfState, getStatesOfCountry } from "@countrystatecity/countries-browser";
import type { ICity, IState } from "@countrystatecity/countries-browser";
import { getIndiaPincode } from "india-pincode/browser";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import {
  checkDeliveryServiceability,
  createPaymentOrder,
  notifyPaymentFailure,
  previewCoupon,
  verifyPayment,
} from "../services/payments";
import type { Product } from "../types";

type CheckoutSectionProps = {
  products: Product[];
};

type IndiaPincodeLookup = Awaited<ReturnType<typeof getIndiaPincode>>;
type IndiaPincodeOffice = {
  area?: string;
  district?: string;
  state?: string;
};

const razorpayKeyId = import.meta.env.VITE_RAZORPAY_KEY_ID ?? "";

function getSessionToken(): string {
  return localStorage.getItem("lagads-user-token") || localStorage.getItem("lagads-admin-token") || "";
}

const initialFormState = {
  customerName: "",
  deliveryAddress: "",
  pincode: "",
  city: "",
  state: "",
  phoneNumber: "",
  email: "",
  alternatePhoneNumber: "",
  comments: "",
  couponCode: ""
};

const indianPhoneRegex = /^[6-9]\d{9}$/;
const indianPincodeRegex = /^[1-9]\d{5}$/;
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function getCheckoutFieldErrors(form: typeof initialFormState) {
  const errors: Partial<Record<keyof typeof initialFormState, string>> = {};

  if (!form.customerName.trim()) {
    errors.customerName = "Full name is required.";
  }
  if (!form.deliveryAddress.trim()) {
    errors.deliveryAddress = "Delivery address is required.";
  }
  if (!form.phoneNumber.trim()) {
    errors.phoneNumber = "Phone number is required.";
  } else if (!indianPhoneRegex.test(form.phoneNumber.trim())) {
    errors.phoneNumber = "Enter a valid 10-digit Indian mobile number.";
  }
  if (form.alternatePhoneNumber.trim() && !indianPhoneRegex.test(form.alternatePhoneNumber.trim())) {
    errors.alternatePhoneNumber = "Enter a valid 10-digit Indian mobile number.";
  }
  if (!form.email.trim()) {
    errors.email = "Email address is required.";
  } else if (!emailRegex.test(form.email.trim())) {
    errors.email = "Enter a valid email address.";
  }
  if (!form.pincode.trim()) {
    errors.pincode = "Pincode is required.";
  } else if (!indianPincodeRegex.test(form.pincode.trim())) {
    errors.pincode = "Enter a valid 6-digit Indian pincode.";
  }
  if (!form.city.trim()) {
    errors.city = "City is required.";
  }
  if (!form.state.trim()) {
    errors.state = "State is required.";
  }

  return errors;
}

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
  const [form, setForm] = useState(initialFormState);
  const [states, setStates] = useState<IState[]>([]);
  const [cities, setCities] = useState<ICity[]>([]);
  const [pincodeLookup, setPincodeLookup] = useState<IndiaPincodeLookup | null>(null);
  const [pincodeSuggestedCity, setPincodeSuggestedCity] = useState("");
  const [autoFillTarget, setAutoFillTarget] = useState<{
    stateIso2: string;
    cityCandidates: string[];
  } | null>(null);
  const [locationLoading, setLocationLoading] = useState(false);
  const [serviceabilityMessage, setServiceabilityMessage] = useState("");
  const [isServiceable, setIsServiceable] = useState<boolean | null>(null);
  const lastRejectedPincode = useRef("");
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState<"success" | "error" | "">("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const paymentFlowLock = useRef(false);
  const [couponDiscountPercent, setCouponDiscountPercent] = useState(0);
  const [couponStatus, setCouponStatus] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof typeof initialFormState, string>>>({});
  const liveFieldErrors = useMemo(() => getCheckoutFieldErrors(form), [form]);
  const hasLiveFieldErrors = Object.keys(liveFieldErrors).length > 0;

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
  const unavailableItems = enrichedCart.filter(
    (item) => item.variant.stockStatus === "out_of_stock" || item.quantity > item.variant.stockQuantity
  );
  const cityOptions = useMemo(() => {
    if (
      pincodeSuggestedCity &&
      !cities.some((city) => city.name.trim().toLowerCase() === pincodeSuggestedCity.trim().toLowerCase())
    ) {
      return [{ id: -1, name: pincodeSuggestedCity } as ICity, ...cities];
    }
    return cities;
  }, [cities, pincodeSuggestedCity]);
  const isCheckoutBlocked =
    isSubmitting ||
    unavailableItems.length > 0 ||
    hasLiveFieldErrors ||
    locationLoading ||
    (form.pincode.trim().length === 6 && isServiceable === false);

  const updateField = (field: keyof typeof form, value: string) => {
    setForm((current) => {
      if (field === "state") {
        return { ...current, state: value, city: "" };
      }
      return { ...current, [field]: value };
    });
    setFieldErrors((current) => {
      if (!current[field]) {
        return current;
      }
      const next = { ...current };
      delete next[field];
      return next;
    });
    if (field === "pincode") {
      setIsServiceable(null);
      setServiceabilityMessage("");
    }
    if (field === "city" || field === "state") {
      setPincodeSuggestedCity("");
    }
  };

  const showStatus = (type: "success" | "error", message: string) => {
    setStatusType(type);
    setStatusMessage(message);
  };

  const validateFields = () => {
    const errors = getCheckoutFieldErrors(form);
    setFieldErrors(errors);
    return errors;
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
    if (unavailableItems.length > 0) {
      return "Some products in your cart are out of stock or exceed the available quantity.";
    }
    if (
      !form.customerName ||
      !form.deliveryAddress ||
      !form.pincode ||
      !form.city ||
      !form.state ||
      !form.phoneNumber ||
      !form.email
    ) {
      return "Please fill all mandatory fields: name, delivery address, pincode, city, state, phone number, and email.";
    }
    const errors = validateFields();
    if (Object.keys(errors).length > 0) {
      return Object.values(errors)[0] || "Please correct the highlighted checkout fields.";
    }
    if (totalAmount < 1) {
      return "Minimum payment amount is Rs. 1.";
    }
    if (form.pincode.trim().length === 6 && isServiceable === false) {
      return "PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION";
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
      if (validationError === "PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION") {
        window.alert("PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION");
      }
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
        pincode: form.pincode,
        city: form.city,
        state: states.find((state) => state.iso2 === form.state)?.name ?? form.state,
        comments: form.comments,
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
            setIsServiceable(null);
            setServiceabilityMessage("");
            setForm(initialFormState);
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
    let cancelled = false;
    setLocationLoading(true);
    void Promise.all([getStatesOfCountry("IN"), getIndiaPincode()])
      .then(([stateResult, pincodeResult]) => {
        if (cancelled) return;
        setStates([...stateResult].sort((left, right) => left.name.localeCompare(right.name)));
        setPincodeLookup(pincodeResult);
      })
      .catch(() => {
        if (cancelled) return;
        showStatus("error", "Unable to load Indian location data right now.");
      })
      .finally(() => {
        if (cancelled) return;
        setLocationLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!form.state) {
      setCities([]);
      return;
    }

    let cancelled = false;
    setLocationLoading(true);
    void getCitiesOfState("IN", form.state)
      .then((result) => {
        if (cancelled) return;
        setCities([...result].sort((left, right) => left.name.localeCompare(right.name)));
      })
      .catch(() => {
        if (cancelled) return;
        setCities([]);
        showStatus("error", "Unable to load cities for the selected state.");
      })
      .finally(() => {
        if (cancelled) return;
        setLocationLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [form.state]);

  useEffect(() => {
    const cleanedPincode = form.pincode.trim();
    if (!pincodeLookup || states.length === 0 || !indianPincodeRegex.test(cleanedPincode)) {
      return;
    }

    type PincodeResult = {
      success?: boolean;
      data?: {
        data?: IndiaPincodeOffice[];
      };
    };

    const result = pincodeLookup.getByPincode(cleanedPincode) as PincodeResult;
    const offices = result?.success ? result.data?.data ?? [] : [];
    if (!offices.length) {
      return;
    }

    const primaryOffice = offices[0];
    const matchedState = states.find(
      (state) => state.name.trim().toLowerCase() === String(primaryOffice.state ?? "").trim().toLowerCase()
    );
    if (!matchedState) {
      return;
    }

    const cityCandidates = Array.from(
      new Set(
        [
          primaryOffice.area?.trim(),
          primaryOffice.district?.trim(),
        ].filter((value): value is string => Boolean(value))
      )
    );

    setPincodeSuggestedCity(cityCandidates[0] ?? "");
    setAutoFillTarget({
      stateIso2: matchedState.iso2,
      cityCandidates,
    });
    setForm((current) => ({
      ...current,
      state: matchedState.iso2,
    }));
  }, [form.pincode, pincodeLookup, states]);

  useEffect(() => {
    if (!autoFillTarget || form.state !== autoFillTarget.stateIso2) {
      return;
    }

    const normalizedCandidates = autoFillTarget.cityCandidates.map((candidate) => candidate.toLowerCase());
    const matchedCity = cities.find((city) => normalizedCandidates.includes(city.name.trim().toLowerCase()));
    const fallbackCity = autoFillTarget.cityCandidates[0] ?? "";
    const nextCity = matchedCity?.name ?? fallbackCity;

    if (!nextCity) {
      return;
    }

    setPincodeSuggestedCity(nextCity);
    setForm((current) => ({
      ...current,
      city: nextCity,
    }));
    setAutoFillTarget(null);
  }, [autoFillTarget, cities, form.state]);

  useEffect(() => {
    const token = getSessionToken();
    const cleanedPincode = form.pincode.trim();
    if (!indianPincodeRegex.test(cleanedPincode)) {
      setIsServiceable(null);
      setServiceabilityMessage("");
      return;
    }

    let cancelled = false;
    void checkDeliveryServiceability(cleanedPincode, token || undefined)
      .then((result) => {
        if (cancelled) return;
        setIsServiceable(result.is_serviceable);
        if (!result.is_serviceable) {
          setServiceabilityMessage("PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION");
          if (lastRejectedPincode.current !== cleanedPincode) {
            window.alert("PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION");
            lastRejectedPincode.current = cleanedPincode;
          }
          return;
        }
        const eta =
          typeof result.estimated_delivery_days === "number"
            ? `Pincode is serviceable. Estimated delivery in ${result.estimated_delivery_days} day${result.estimated_delivery_days === 1 ? "" : "s"}.`
            : "Pincode is serviceable.";
        setServiceabilityMessage(eta);
        lastRejectedPincode.current = "";
      })
      .catch((error) => {
        if (cancelled) return;
        const message =
          error instanceof Error ? error.message : "Unable to verify delivery serviceability.";
        if (message === "PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION") {
          setIsServiceable(false);
          setServiceabilityMessage(message);
          if (lastRejectedPincode.current !== cleanedPincode) {
            window.alert("PINCODE IS NOT YET IN OUR SERVICEBALE LOCATION");
            lastRejectedPincode.current = cleanedPincode;
          }
          return;
        }
        setIsServiceable(null);
        setServiceabilityMessage(message);
      });

    return () => {
      cancelled = true;
    };
  }, [form.pincode]);

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
  }, [form.couponCode, totalAmount]);

  return (
    <section className="checkout-shell" id="checkout">
      <div>
        <p className="eyebrow">Checkout workflow</p>
        <h2>Fill customer details and review the final order summary before payment</h2>
        <p>
          All checkout details except the coupon code are mandatory. The final product breakup and
          payable amount appear below the form before the payment gateway opens.
        </p>
        <p className="muted">
          Choose the state first, then select the exact city or suburb from the dropdown list.
        </p>
        <p className="muted">
          Product prices are inclusive of all taxes. Delivery charges are not included in the item
          price and are currently applied as FREE at checkout.
        </p>
        {user ? (
          <p className="muted">
            Logged-in users also get order history in their account after successful payment.
          </p>
        ) : null}
      </div>

      <div className="checkout-form">
        <form className="checkout-details-card">
          <label className="field">
            <span>Full Name</span>
            <input
              placeholder="Enter full name"
              value={form.customerName}
              onChange={(event) => updateField("customerName", event.target.value)}
            />
            {liveFieldErrors.customerName ? <span className="field-error">{liveFieldErrors.customerName}</span> : null}
          </label>
          <label className="field">
            <span>Delivery Address</span>
            <textarea
              placeholder="House number, street, locality, landmark"
              rows={4}
              value={form.deliveryAddress}
              onChange={(event) => updateField("deliveryAddress", event.target.value)}
            />
            {liveFieldErrors.deliveryAddress ? <span className="field-error">{liveFieldErrors.deliveryAddress}</span> : null}
          </label>
          <div className="checkout-location-grid">
            <label className="field">
              <span>State</span>
              <select
                value={form.state}
                onChange={(event) => updateField("state", event.target.value)}
                disabled={locationLoading}
              >
                <option value="">{locationLoading && states.length === 0 ? "Loading states..." : "Select state"}</option>
                {states.map((state) => (
                  <option key={state.iso2} value={state.iso2}>
                    {state.name}
                  </option>
                ))}
              </select>
              {liveFieldErrors.state ? <span className="field-error">{liveFieldErrors.state}</span> : null}
            </label>
            <label className="field">
              <span>City / Suburb</span>
              <select
                value={form.city}
                onChange={(event) => updateField("city", event.target.value)}
                disabled={!form.state || locationLoading}
              >
                <option value="">
                  {!form.state ? "Select state first" : locationLoading ? "Loading cities..." : "Select city / suburb"}
                </option>
                {cityOptions.map((city) => (
                  <option key={city.id} value={city.name}>
                    {city.name}
                  </option>
                ))}
              </select>
              {liveFieldErrors.city ? <span className="field-error">{liveFieldErrors.city}</span> : null}
            </label>
          </div>
          <label className="field">
            <span>Pincode</span>
            <input
              inputMode="numeric"
              maxLength={6}
              placeholder="Enter delivery pincode"
              value={form.pincode}
              onChange={(event) => updateField("pincode", event.target.value.replace(/\D/g, "").slice(0, 6))}
            />
            {liveFieldErrors.pincode ? <span className="field-error">{liveFieldErrors.pincode}</span> : null}
          </label>
          {serviceabilityMessage ? (
            <p className={`status-message ${isServiceable === false ? "error" : "success"}`}>
              {serviceabilityMessage}
            </p>
          ) : null}
          <label className="field">
            <span>Phone Number</span>
            <input
              inputMode="numeric"
              maxLength={10}
              placeholder="Primary mobile number"
              value={form.phoneNumber}
              onChange={(event) => updateField("phoneNumber", event.target.value.replace(/\D/g, "").slice(0, 10))}
            />
            {liveFieldErrors.phoneNumber ? <span className="field-error">{liveFieldErrors.phoneNumber}</span> : null}
          </label>
          <label className="field">
            <span>Email Address</span>
            <input
              type="email"
              placeholder="your@email.com"
              value={form.email}
              onChange={(event) => updateField("email", event.target.value.trim())}
            />
            {liveFieldErrors.email ? <span className="field-error">{liveFieldErrors.email}</span> : null}
          </label>
          <label className="field">
            <span>Alternative Phone Number</span>
            <input
              inputMode="numeric"
              maxLength={10}
              placeholder="Optional alternate mobile number"
              value={form.alternatePhoneNumber}
              onChange={(event) =>
                updateField("alternatePhoneNumber", event.target.value.replace(/\D/g, "").slice(0, 10))
              }
            />
            {liveFieldErrors.alternatePhoneNumber ? (
              <span className="field-error">{liveFieldErrors.alternatePhoneNumber}</span>
            ) : null}
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
              placeholder="Optional delivery notes or request"
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
        </form>

        <div className="checkout-order-card">
          <div className="checkout-order-header">
            <div>
              <span className="eyebrow">Order Summary</span>
              <h3>
                {itemCount} Item{itemCount === 1 ? "" : "s"}
              </h3>
            </div>
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
                    <strong>{item.product.fullName}</strong>
                    <p>
                      {item.variant.weight} x {item.quantity}
                    </p>
                    <p className="muted">
                      MRP {formatRupees(item.variant.mrp)} | {item.variant.discountPercentage}% off |
                      Selling {formatRupees(item.variant.sellingPrice)} (inclusive of all taxes)
                    </p>
                    {item.variant.stockStatus === "out_of_stock" ? (
                      <p className="status-message error">Out of stock</p>
                    ) : item.quantity > item.variant.stockQuantity ? (
                      <p className="status-message error">
                        Only {item.variant.stockQuantity} item(s) available for this variant.
                      </p>
                    ) : null}
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
          <p className="muted">Expected Delivery: 3–7 business days</p>
          {unavailableItems.length > 0 ? (
            <p className="status-message error">
              Some cart items are no longer available in the requested quantity. Please update your cart before payment.
            </p>
          ) : null}
          {hasLiveFieldErrors ? (
            <p className="status-message error">
              Please correct the highlighted customer details before continuing to the payment gateway.
            </p>
          ) : null}

          <button
            type="button"
            className="pill pill-primary"
            onClick={handlePayment}
            disabled={isCheckoutBlocked}
          >
            {isSubmitting ? "Opening Payment..." : "Continue to Payment Gateway"}
          </button>
          {statusMessage ? <p className={`status-message ${statusType}`}>{statusMessage}</p> : null}
        </div>
      </div>
    </section>
  );
}
