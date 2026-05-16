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
      <div className="hero-actions hero-actions-fixed">
        <a className="pill pill-primary" href="#products">
          Shop Now
        </a>
      </div>
    </section>
  );
}
