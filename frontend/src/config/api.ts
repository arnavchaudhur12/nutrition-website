const configuredApiOrigin = import.meta.env.VITE_API_ORIGIN ?? "http://localhost:8000";

export const API_ORIGIN = configuredApiOrigin.replace(/\/$/, "");
export const API_BASE_URL = `${API_ORIGIN}/api`;
