export type AdminProductVariant = {
  id: number;
  weight_label: string;
  mrp: number;
  selling_price: number;
  stock_quantity: number;
};

export type AdminProduct = {
  id: number;
  slug: string;
  name: string;
  flavour: string;
  description: string;
  image_url?: string | null;
  category: string;
  variants: AdminProductVariant[];
};

