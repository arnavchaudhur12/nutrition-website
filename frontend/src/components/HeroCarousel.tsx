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

  const fallbackImage = "/hero-quote-background.jpeg";
  const desktopSlides = desktopImages.length > 0 ? desktopImages : [fallbackImage];
  const mobileSlides = mobileImages.length > 0 ? mobileImages : desktopSlides;
  const slideCount = Math.max(desktopSlides.length, mobileSlides.length);
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    setCurrentSlide(0);
    const timer = window.setInterval(() => {
      setCurrentSlide((previous) => (previous + 1) % slideCount);
    }, 2000);

    return () => window.clearInterval(timer);
  }, [slideCount, hero.images]);

  const desktopHeroImage = desktopSlides[currentSlide % desktopSlides.length] ?? fallbackImage;
  const mobileHeroImage = mobileSlides[currentSlide % mobileSlides.length] ?? desktopHeroImage;

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
