import { useEffect, useState } from "react";
import { resolveHeroImageUrl } from "../services/hero";
import type { HeroConfig } from "../types/hero";

export function HeroCarousel({ hero }: { hero: HeroConfig | null }) {
  if (!hero) {
    return null;
  }

  const desktopImages = hero.images
    .filter((image) => image.sort_order >= 0 && image.sort_order < 3)
    .sort((left, right) => left.sort_order - right.sort_order)
    .map((image) => resolveHeroImageUrl(image.image_url))
    .filter((image): image is string => Boolean(image));
  const mobileImages = hero.images
    .filter((image) => image.sort_order >= 3 && image.sort_order < 6)
    .sort((left, right) => left.sort_order - right.sort_order)
    .map((image) => resolveHeroImageUrl(image.image_url))
    .filter((image): image is string => Boolean(image));

  const slideCount = Math.max(desktopImages.length, mobileImages.length);
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    if (slideCount === 0) {
      setCurrentSlide(0);
      return undefined;
    }

    setCurrentSlide(0);
    const timer = window.setInterval(() => {
      setCurrentSlide((previous) => (previous + 1) % slideCount);
    }, 3000);

    return () => window.clearInterval(timer);
  }, [slideCount, hero.images]);

  const desktopHeroImage =
    desktopImages.length > 0 ? desktopImages[currentSlide % desktopImages.length] : null;
  const mobileHeroImage =
    mobileImages.length > 0 ? mobileImages[currentSlide % mobileImages.length] : null;
  const rawCtaLink = (hero.cta_link || "").trim();
  const isExternalCta = /^(?:[a-z][a-z0-9+.-]*:)?\/\//i.test(rawCtaLink)
    || /^(mailto:|tel:)/i.test(rawCtaLink);
  const isInternalCta = !rawCtaLink || !isExternalCta;

  const scrollToProducts = () => {
    const normalizedTarget = rawCtaLink
      .replace(/^https?:\/\/[^/]+/i, "")
      .replace(/^\/+/, "")
      .replace(/^#/, "");
    const preferredTargetId = normalizedTarget || "products-start";
    const target =
      document.getElementById(preferredTargetId) ||
      document.getElementById(preferredTargetId.replace(/^products$/, "products-start")) ||
      document.getElementById("products-start") ||
      document.getElementById("products");

    if (!target) {
      return;
    }

    target.scrollIntoView({ behavior: "smooth", block: "start" });
    window.history.replaceState(null, "", "#products-start");
  };

  const handleInternalCtaClick = () => {
    scrollToProducts();
  };

  return (
    <section className="hero">
      {(desktopHeroImage || mobileHeroImage) && (
        <div className="hero-background-picture">
          {desktopHeroImage && (
            <img
              src={desktopHeroImage}
              alt={hero.headline}
              className="hero-background-image hero-background-image-desktop"
            />
          )}
          {mobileHeroImage && (
            <img
              src={mobileHeroImage}
              alt={hero.headline}
              className="hero-background-image hero-background-image-mobile"
            />
          )}
        </div>
      )}
      <div className="hero-actions hero-actions-fixed">
        {isInternalCta ? (
          <button type="button" className="pill pill-primary hero-cta-button" onClick={handleInternalCtaClick}>
            {hero.cta_label || "Shop Now"}
          </button>
        ) : (
          <a className="pill pill-primary" href={rawCtaLink}>
            {hero.cta_label || "Shop Now"}
          </a>
        )}
      </div>
    </section>
  );
}
