import { resolveHeroImageUrl } from "../services/hero";
import type { HeroConfig } from "../types/hero";

export function HeroCarousel({ hero }: { hero: HeroConfig | null }) {
  if (!hero) {
    return null;
  }

  const desktopHeroImage =
    resolveHeroImageUrl(hero.images[0]?.image_url) ?? "/hero-quote-background.jpeg";
  const mobileHeroImage = resolveHeroImageUrl(hero.images[1]?.image_url) ?? desktopHeroImage;

  return (
    <section className="hero">
      <picture className="hero-background-picture">
        <source media="(max-width: 900px)" srcSet={mobileHeroImage} />
        <img src={desktopHeroImage} alt={hero.headline} className="hero-background-image" />
      </picture>
      <div className="hero-actions hero-actions-fixed">
        <a className="pill pill-primary" href={hero.cta_link || "#products"}>
          {hero.cta_label || "Shop Now"}
        </a>
      </div>
    </section>
  );
}
