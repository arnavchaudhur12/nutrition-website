import { useCart } from "../context/CartContext";
import type { Product } from "../types";
import { Icon } from "./Icon";

type CartDrawerProps = {
  open: boolean;
  onClose: () => void;
  products: Product[];
};

export function CartDrawer({ open, onClose, products }: CartDrawerProps) {
  const { items, removeItem } = useCart();

  const enriched = items.map((item) => {
    const product = products.find((candidate) => candidate.id === item.productId);
    const variant = product?.variants.find((candidate) => candidate.id === item.variantId);
    return product && variant ? { ...item, product, variant } : null;
  }).filter((item): item is NonNullable<typeof item> => Boolean(item));
  const hasBlockedItems = enriched.some(
    (item) => item.variant.stockStatus === "out_of_stock" || item.quantity > item.variant.stockQuantity
  );

  const total = enriched.reduce(
    (sum, item) => sum + item.variant.sellingPrice * item.quantity,
    0
  );

  return (
    <aside className={`panel cart-panel ${open ? "open" : ""}`}>
      <div className="drawer-header">
        <h2>Your Cart</h2>
        <button className="icon-button" onClick={onClose} aria-label="Close cart">
          <Icon name="close" />
        </button>
      </div>
      <div className="cart-list">
        {enriched.length === 0 ? (
          <p className="muted">No items added yet.</p>
        ) : (
          enriched.map((item) => (
            <article key={`${item.productId}-${item.variantId}`} className="cart-item">
              <div>
                <h3>{item.product.fullName}</h3>
                <p>
                  {item.variant.weight} x {item.quantity}
                </p>
                {item.variant.stockStatus === "out_of_stock" ? (
                  <p className="status-message error">Out of stock</p>
                ) : item.quantity > item.variant.stockQuantity ? (
                  <p className="status-message error">Only {item.variant.stockQuantity} item(s) available</p>
                ) : (
                  <p className="muted">
                    {item.variant.discountPercentage}% off, inclusive of all taxes
                  </p>
                )}
                <strong>Rs. {item.variant.sellingPrice * item.quantity}</strong>
              </div>
              <button
                className="text-button"
                onClick={() => removeItem(item.productId, item.variantId)}
              >
                Remove
              </button>
            </article>
          ))
        )}
      </div>
      <div className="cart-footer">
        <p className="muted">No delivery charges</p>
        <div className="cart-total">
          <span>Total</span>
          <strong>Rs. {total}</strong>
        </div>
        <a
          className="pill pill-primary"
          href={hasBlockedItems ? undefined : "#checkout"}
          onClick={hasBlockedItems ? (event) => event.preventDefault() : onClose}
          aria-disabled={hasBlockedItems}
        >
          Proceed to Checkout
        </a>
        {hasBlockedItems ? <p className="status-message error">Remove out-of-stock items before checkout.</p> : null}
      </div>
    </aside>
  );
}
