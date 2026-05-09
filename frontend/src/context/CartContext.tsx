import { createContext, useContext, useMemo, useState } from "react";
import type { CartItem } from "../types";

type CartContextValue = {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (productId: string, variantId: string) => void;
  itemCount: number;
};

const CartContext = createContext<CartContextValue | undefined>(undefined);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);

  const addItem = (incoming: CartItem) => {
    setItems((current) => {
      const existing = current.find(
        (item) =>
          item.productId === incoming.productId && item.variantId === incoming.variantId
      );

      if (existing) {
        return current.map((item) =>
          item.productId === incoming.productId && item.variantId === incoming.variantId
            ? { ...item, quantity: item.quantity + incoming.quantity }
            : item
        );
      }

      return [...current, incoming];
    });
  };

  const removeItem = (productId: string, variantId: string) => {
    setItems((current) =>
      current.filter(
        (item) => !(item.productId === productId && item.variantId === variantId)
      )
    );
  };

  const itemCount = useMemo(
    () => items.reduce((total, item) => total + item.quantity, 0),
    [items]
  );

  return (
    <CartContext.Provider value={{ items, addItem, removeItem, itemCount }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within CartProvider");
  }
  return context;
}

