import { createContext, useContext, useState, ReactNode } from "react";
import { api, Role } from "../api/client";

// Temporary: skips the login gate entirely. The backend separately skips
// token verification when AUTH_DISABLED=true in its own env (see
// backend/app/deps.py::get_current_user) -- both sides must agree, since
// this only controls what the frontend *shows*; the API would still 401
// every request if the backend weren't also told to skip auth. Flip this
// back to false to re-require login.
const AUTH_DISABLED = true;

interface AuthState {
  role: Role | null;
  fullName: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role | null>(
    (localStorage.getItem("role") as Role | null) ?? (AUTH_DISABLED ? "admin" : null)
  );
  const [fullName, setFullName] = useState<string | null>(
    localStorage.getItem("full_name") ?? (AUTH_DISABLED ? "Everyone (login disabled)" : null)
  );

  async function login(email: string, password: string) {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("access_token", res.data.access_token);
    localStorage.setItem("role", res.data.role);
    localStorage.setItem("full_name", res.data.full_name);
    setRole(res.data.role);
    setFullName(res.data.full_name);
  }

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("role");
    localStorage.removeItem("full_name");
    setRole(AUTH_DISABLED ? "admin" : null);
    setFullName(AUTH_DISABLED ? "Everyone (login disabled)" : null);
  }

  return (
    <AuthContext.Provider value={{ role, fullName, isAuthenticated: AUTH_DISABLED || !!role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
