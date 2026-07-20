type IconProps = {
  name: "menu" | "account" | "cart" | "close" | "box" | "truck";
};

export function Icon({ name }: IconProps) {
  const icons: Record<IconProps["name"], string> = {
    menu: "☰",
    account: "◯",
    cart: "👜",
    close: "✕",
    box: "▣",
    truck: "🚚"
  };

  return <span aria-hidden="true">{icons[name]}</span>;
}
