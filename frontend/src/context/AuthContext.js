import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, tokenStore } from "../lib/api";

const AuthContext = createContext(null);
export const ROLES = { ADMIN: "Administrator", ENGINEER: "Network Engineer", AUDITOR: "Auditor" };

export function AuthProvider({ children }) {
  const [user, setUser] = useState(tokenStore.get() ? null : false);

  useEffect(() => {
    if (!tokenStore.get()) return;
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => setUser(false));
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(false);
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  const login = useCallback(async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    tokenStore.set(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      tokenStore.clear();
      setUser(false);
    }
  }, []);

  const hasRole = useCallback((...roles) => Boolean(user && roles.includes(user.role)), [user]);

  return <AuthContext.Provider value={{ user, login, logout, hasRole }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
