import { useState } from "react";
import { useCart } from "../context/CartContext";
import type { Product } from "../types";

export function ProductCard({ product }: { product: Product }) {
  const { addItem } = useCart();
  const [variantId, setVariantId] = useState(product.variants[0].id);
  const [quantity, setQuantity] = useState(1);
  const [imageIndex, setImageIndex] = useState(0);

  const variant = product.variants.find((item) => item.id === variantId) ?? product.variants[0];
  const dynamicTotal = variant.sellingPrice * quantity;
  const visibleImage = product.images[imageIndex] ?? product.image;

  return (
    <article className="product-card" id={product.id}>
      <div className="product-visual">
        <img src={visibleImage} alt={product.flavour} />
        {product.images.length > 1 ? (
          <button
            type="button"
            className="carousel-arrow carousel-arrow-right product-carousel-arrow"
            aria-label={`Show next image for ${product.flavour}`}
            onClick={() => setImageIndex((current) => (current + 1) % product.images.length)}
          >
            ›
          </button>
        ) : null}
      </div>
      <div className="product-body">
        <p className="eyebrow">Peanut Butter</p>
        <h3>{product.flavour}</h3>
        <p className="product-description">{product.description}</p>

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
          <label className="quantity-stepper">
            <span>Qty</span>
            <input
              type="number"
              min={1}
              value={quantity}
              onChange={(event) => setQuantity(Math.max(1, Number(event.target.value) || 1))}
            />
          </label>
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
    </article>
  );
}
