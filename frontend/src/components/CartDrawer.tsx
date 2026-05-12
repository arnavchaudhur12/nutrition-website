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
                <h3>{item.product.flavour}</h3>
                <p>
                  {item.variant.weight} x {item.quantity}
                </p>
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
        <div className="cart-total">
          <span>Total</span>
          <strong>Rs. {total}</strong>
        </div>
        <a className="pill pill-primary" href="#checkout" onClick={onClose}>
          Proceed to Checkout
        </a>
      </div>
    </aside>
  );
}
