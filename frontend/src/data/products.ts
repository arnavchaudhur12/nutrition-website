import logo from "../assets/company-logo.png";
import type { Product } from "../types";

const descriptionBase =
  "Lagads Nutrition peanut butter is designed for customers who want a richer, more satisfying everyday spread without compromising on consistency, taste, or convenience. Each batch is crafted for a smooth spoon feel, dependable texture, and indulgent flavour that works beautifully in breakfast bowls, smoothies, toast, shakes, desserts, or straight from the jar. The Dark Chocolate Crispy range brings together a roasted peanut body with chocolate depth and a pleasant crunch that keeps each serving exciting. The Mawa Malai Creamy range is softer, fuller, and dessert-inspired, built for customers who prefer a mellow, creamy finish with a comforting profile. Across both flavours, the goal is simple: premium taste, repeatable quality, and packaging sizes that suit both regular personal use and family consumption. Whether a customer chooses the 500g trial-friendly pack or the 1kg value pack, the experience should feel generous, consistent, and worth reordering. This product line is positioned as a standout pantry staple for fitness-conscious customers, families, and snack lovers looking for flavour-forward nutrition products from an Indian brand with personality.";

export const products: Product[] = [
  {
    id: "dark-chocolate-crispy",
    name: "Peanut Butter",
    flavour: "Dark Chocolate Crispy",
    accent: "#ff7a00",
    heroTitle: "Crunch that keeps the spoon coming back",
    heroSubtitle: "Premium roasted peanut butter with deep chocolate notes.",
    description: descriptionBase,
    image: logo,
    images: [logo],
    highlights: ["High-repeat flavour", "Crunchy texture", "Daily-use pantry jar"],
    variants: [
      {
        id: "dcc-1kg",
        label: "1kg",
        weight: "1kg",
        mrp: 699,
        sellingPrice: 500,
        stockStatus: "in_stock"
      },
      {
        id: "dcc-500g",
        label: "500g",
        weight: "500g",
        mrp: 375,
        sellingPrice: 350,
        stockStatus: "in_stock"
      }
    ]
  },
  {
    id: "mawa-malai-creamy",
    name: "Peanut Butter",
    flavour: "Mawa Malai Creamy",
    accent: "#f0a04b",
    heroTitle: "Dessert-inspired richness in every spread",
    heroSubtitle: "Creamy, mellow and indulgent for everyday use.",
    description: descriptionBase,
    image: logo,
    images: [logo],
    highlights: ["Creamy mouthfeel", "Mellow finish", "Perfect for shakes and toast"],
    variants: [
      {
        id: "mmc-1kg",
        label: "1kg",
        weight: "1kg",
        mrp: 719,
        sellingPrice: 530,
        stockStatus: "in_stock"
      },
      {
        id: "mmc-500g",
        label: "500g",
        weight: "500g",
        mrp: 389,
        sellingPrice: 370,
        stockStatus: "in_stock"
      }
    ]
  }
];
