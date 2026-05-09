type IconProps = {
  name: "menu" | "account" | "cart" | "close";
};

export function Icon({ name }: IconProps) {
  const icons: Record<IconProps["name"], string> = {
    menu: "☰",
    account: "◯",
    cart: "👜",
    close: "✕"
  };

  return <span aria-hidden="true">{icons[name]}</span>;
}

