import axios from "axios";

export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TOKEN_KEY = "mpls_copilot_token";

// Token kept in sessionStorage (cleared when the tab closes) and revoked server-side on logout.
export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (t) => sessionStorage.setItem(TOKEN_KEY, t),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

export const api = axios.create({ baseURL: API, timeout: 30000 });

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes("/auth/login")) {
      tokenStore.clear();
      window.dispatchEvent(new Event("auth:expired"));
    }
    return Promise.reject(error);
  },
);

export function errMsg(error) {
  const detail = error?.response?.data?.detail;
  if (!detail) return error?.response?.status === 403 ? "You are not permitted to do that." : error?.message || "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => `${(d.loc || []).slice(-1)[0] || "field"}: ${d.msg}`).join("; ");
  return String(detail);
}

export function cleanParams(params) {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v !== null && v !== undefined));
}

export async function downloadFile(path, params, filename) {
  const response = await api.get(path, { params: cleanParams(params), responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// Server timestamps are naive UTC (MySQL DATETIME); mark them as UTC before formatting.
export const fmtDate = (iso) => (iso ? new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "—");
