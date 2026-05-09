import { useEffect, useState } from "react";
import { products } from "../data/products";

export function HeroCarousel() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % products.length);
    }, 5000);
    return () => window.clearInterval(timer);
  }, []);

  const product = products[index];

  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Small-batch flavour. Big shelf presence.</p>
        <h2>{product.heroTitle}</h2>
        <p>{product.heroSubtitle}</p>
        <div className="hero-actions">
          <a className="pill pill-primary" href="#products">
            Shop Now
          </a>
          <span className="hero-offer">Fresh jars. Strong value. Smooth checkout.</span>
        </div>
      </div>

      <div className="hero-visual">
        <img src={product.image} alt={product.flavour} />
        <div className="hero-card">
          <span>{product.flavour}</span>
          <strong>Starts at Rs. {Math.min(...product.variants.map((variant) => variant.sellingPrice))}</strong>
        </div>
      </div>
    </section>
  );
}

