import type { HeroConfig } from "../types/hero";

const desktopHeroImage = new URL(
  "../../../all_images/global_images/website_font/ChatGPT Image May 22, 2026, 02_11_24 PM.png",
  import.meta.url
).href;
const mobileHeroImage = new URL(
  "../../../all_images/global_images/mobile_font/IMG_0608.PNG",
  import.meta.url
).href;

export function HeroCarousel({ hero }: { hero: HeroConfig | null }) {
  if (!hero) {
    return null;
  }

  return (
    <section className="hero">
      <picture className="hero-background-picture">
        <source media="(max-width: 900px)" srcSet={mobileHeroImage} />
        <img src={desktopHeroImage} alt={hero.headline} className="hero-background-image" />
      </picture>
      <div className="hero-actions hero-actions-fixed">
        <a className="pill pill-primary" href="#products">
          Shop Now
        </a>
      </div>
    </section>
  );
}
