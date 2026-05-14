import { useEffect, useState } from "react";
import { resolveHeroImageUrl } from "../services/hero";
import type { HeroConfig } from "../types/hero";

export function HeroCarousel({ hero }: { hero: HeroConfig | null }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!hero || hero.images.length <= 1) {
      return;
    }
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % hero.images.length);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [hero]);

  useEffect(() => {
    if (!hero || index >= hero.images.length) {
      setIndex(0);
    }
  }, [hero, index]);

  if (!hero) {
    return null;
  }
  const imageUrl = resolveHeroImageUrl(hero.images[index]?.image_url) ?? "/hero-quote-background.jpeg";

  return (
    <section className="hero">
      <img src={imageUrl} alt={hero.headline} className="hero-background-image" />
      <div className="hero-copy">
        <p className="eyebrow">{hero.eyebrow_text}</p>
        <h2>{hero.headline}</h2>
        <p>{hero.body_text}</p>
        <div className="hero-actions">
          <a className="pill pill-primary" href="#products">
            {hero.cta_label}
          </a>
          <span className="hero-offer">{hero.offer_text}</span>
        </div>
      </div>

      <div className="hero-card">
        <span>{hero.badge_title}</span>
        <strong>{hero.badge_subtitle}</strong>
      </div>
    </section>
  );
}
