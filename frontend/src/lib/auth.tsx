"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User } from "@/lib/types";
import { fetchWithAuth, clearToken, setToken } from "@/lib/api";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterPayload) => Promise<User>;
  logout: () => void;
  isAdmin: boolean;
}

interface RegisterPayload {
  full_name: string;
  email: string;
  password: string;
  college?: string;
  department?: string;
  degree?: string;
  graduation_year?: number;
  location?: string;
  target_role_id?: string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const u = await fetchWithAuth();
      setUser(u);
      localStorage.setItem("user_id", u.id);
      localStorage.setItem("user", JSON.stringify(u));
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const api = (await import("@/lib/api")).api;
    const { data } = await api.post("/auth/login", { email, password });
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("user_id", data.user.id);
    localStorage.setItem("user", JSON.stringify(data.user));
  };

  const register = async (data: RegisterPayload) => {
    const api = (await import("@/lib/api")).api;
    const { data: res } = await api.post("/auth/register", data);
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem("user_id", res.user.id);
    return res.user;
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
