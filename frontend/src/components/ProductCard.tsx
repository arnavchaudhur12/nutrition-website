import { useRef, useState } from "react";
import type { TouchEvent } from "react";
import { useCart } from "../context/CartContext";
import type { Product } from "../types";

export function ProductCard({ product }: { product: Product }) {
  const { addItem } = useCart();
  const [variantId, setVariantId] = useState(product.variants[0].id);
  const [quantity, setQuantity] = useState(1);
  const [imageIndex, setImageIndex] = useState(0);
  const [descriptionOpen, setDescriptionOpen] = useState(false);
  const touchStartX = useRef<number | null>(null);

  const variant = product.variants.find((item) => item.id === variantId) ?? product.variants[0];
  const dynamicTotal = variant.sellingPrice * quantity;
  const visibleImage = product.images[imageIndex] ?? product.image;
  const hasMultipleImages = product.images.length > 1;

  const cycleImages = (direction: 1 | -1) => {
    if (!hasMultipleImages) {
      return;
    }
    setImageIndex((current) => (current + direction + product.images.length) % product.images.length);
  };

  const handleTouchStart = (event: TouchEvent<HTMLDivElement>) => {
    touchStartX.current = event.changedTouches[0]?.clientX ?? null;
  };

  const handleTouchEnd = (event: TouchEvent<HTMLDivElement>) => {
    const startX = touchStartX.current;
    const endX = event.changedTouches[0]?.clientX;
    touchStartX.current = null;

    if (startX === null || endX === undefined) {
      return;
    }

    const deltaX = endX - startX;
    if (Math.abs(deltaX) < 36) {
      return;
    }

    cycleImages(deltaX < 0 ? 1 : -1);
  };

  return (
    <article className="product-card" id={product.id}>
      <div className="product-visual" onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
        <img src={visibleImage} alt={product.flavour} />
        {hasMultipleImages ? (
          <div className="product-gallery-dots" aria-label={`${product.flavour} image gallery`}>
            {product.images.map((image, currentImageIndex) => (
              <button
                key={image}
                type="button"
                className={`gallery-dot ${currentImageIndex === imageIndex ? "active" : ""}`}
                aria-label={`Show image ${currentImageIndex + 1} for ${product.flavour}`}
                aria-pressed={currentImageIndex === imageIndex}
                onClick={() => setImageIndex(currentImageIndex)}
              />
            ))}
          </div>
        ) : null}
      </div>
      <div className="product-body">
        <p className="eyebrow">Peanut Butter</p>
        <h3>{product.flavour}</h3>
        <button
          type="button"
          className="product-description-trigger"
          onClick={() => setDescriptionOpen(true)}
        >
          Product Description
        </button>

        <div className="chip-row">
          {product.highlights.map((item) => (
            <span key={item} className="chip">
              {item}
            </span>
          ))}
        </div>

        <label className="field">
          <span>Choose size</span>
          <select value={variantId} onChange={(event) => setVariantId(event.target.value)}>
            {product.variants.map((item) => (
              <option key={item.id} value={item.id}>
                {item.weight} - Rs. {item.sellingPrice}
              </option>
            ))}
          </select>
        </label>

        <div className="price-row">
          <div>
            <strong>Rs. {variant.sellingPrice}</strong>
            <span className="strikethrough">Rs. {variant.mrp}</span>
          </div>
          <div className="quantity-stepper">
            <span>Qty</span>
            <div className="quantity-stepper-controls" aria-label={`Quantity for ${product.flavour}`}>
              <button
                type="button"
                className="quantity-stepper-button"
                aria-label={`Decrease quantity for ${product.flavour}`}
                onClick={() => setQuantity((current) => Math.max(1, current - 1))}
              >
                -
              </button>
              <span className="quantity-stepper-value" aria-live="polite">
                {quantity}
              </span>
              <button
                type="button"
                className="quantity-stepper-button"
                aria-label={`Increase quantity for ${product.flavour}`}
                onClick={() => setQuantity((current) => current + 1)}
              >
                +
              </button>
            </div>
          </div>
        </div>

        <div className="checkout-row">
          <span>Total: Rs. {dynamicTotal}</span>
          <button
            className="pill pill-primary"
            onClick={() =>
              addItem({
                productId: product.id,
                variantId,
                quantity
              })
            }
          >
            Add to Cart
          </button>
        </div>
      </div>

      {descriptionOpen ? (
        <div
          className="terms-modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-label={`${product.flavour} description`}
          onClick={() => setDescriptionOpen(false)}
        >
          <div className="terms-modal-card product-description-modal" onClick={(event) => event.stopPropagation()}>
            <div className="terms-modal-header">
              <h3>{product.flavour}</h3>
              <button
                type="button"
                className="icon-button"
                onClick={() => setDescriptionOpen(false)}
                aria-label={`Close description for ${product.flavour}`}
              >
                x
              </button>
            </div>
            <div className="terms-modal-content">
              <p>{product.description}</p>
            </div>
          </div>
        </div>
      ) : null}
    </article>
  );
}
