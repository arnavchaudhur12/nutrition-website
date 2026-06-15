import { useEffect, useState } from "react";
import { resolveHeroImageUrl } from "../services/hero";
import type { HeroConfig } from "../types/hero";

export function HeroCarousel({ hero }: { hero: HeroConfig | null }) {
  if (!hero) {
    return null;
  }

  const desktopImages = hero.images
    .slice(0, 3)
    .map((image) => resolveHeroImageUrl(image.image_url))
    .filter((image): image is string => Boolean(image));
  const mobileImages = hero.images
    .slice(3, 6)
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
        <a className="pill pill-primary" href={hero.cta_link || "#products"}>
          {hero.cta_label || "Shop Now"}
        </a>
      </div>
    </section>
  );
}
