export type ProductVariant = {
  id: string;
  label: string;
  weight: string;
  mrp: number;
  sellingPrice: number;
  stockStatus: "in_stock" | "low_stock" | "out_of_stock";
};

export type Product = {
  id: string;
  name: string;
  flavour: string;
  accent: string;
  heroTitle: string;
  heroSubtitle: string;
  description: string;
  image: string;
  images: string[];
  variants: ProductVariant[];
  highlights: string[];
};

export type CartItem = {
  productId: string;
  variantId: string;
  quantity: number;
};
