const resolveApiOrigin = () => {
  if (import.meta.env.VITE_API_ORIGIN) {
    return import.meta.env.VITE_API_ORIGIN;
  }

  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }

  const { hostname, origin } = window.location;
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://localhost:8000";
  }

  return origin;
};

const configuredApiOrigin = resolveApiOrigin();

export const API_ORIGIN = configuredApiOrigin.replace(/\/$/, "");
export const API_BASE_URL = `${API_ORIGIN}/api`;
