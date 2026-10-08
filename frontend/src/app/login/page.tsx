"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Mail, Lock, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <div className="card">
        <div className="card-header">
          <h1 className="card-title">Sign in</h1>
          <p className="card-sub">Welcome back — continue your roadmap</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field pl-9"
                placeholder="you@college.edu"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field pl-9"
                placeholder="••••••••"
                required
                minLength={6}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
        <div className="mt-6 text-center text-sm text-navy-600">
          New here?{" "}
          <Link href="/register" className="text-accent-400 font-medium hover:underline">
            Create an account
          </Link>
        </div>
        <div className="mt-4 rounded-xl bg-navy-100 border border-navy-200 p-4">
          <p className="text-xs font-medium text-navy-600 uppercase tracking-wider mb-1">Demo credentials</p>
          <p className="text-sm text-navy-800 font-mono">
            student@demo.local / demo1234
          </p>
        </div>
      </div>
    </div>
  );
}
