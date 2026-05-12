export type HeroImage = {
  id: number;
  image_url: string;
  sort_order: number;
};

export type HeroConfig = {
  eyebrow_text: string;
  headline: string;
  body_text: string;
  cta_label: string;
  cta_link: string;
  offer_text: string;
  badge_title: string;
  badge_subtitle: string;
  images: HeroImage[];
};
