"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-surface-line bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex items-center gap-0.5">
              <div className="w-3 h-3 rounded-full bg-accent-400" />
              <div className="w-3 h-3 rounded-full bg-navy-500" />
              <div className="w-3 h-3 rounded-full bg-navy-700" />
            </div>
            <span className="text-lg font-semibold text-navy-900 tracking-tight">
              Skill<span className="text-accent-400">Intel</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {user?.role === "admin" && (
              <Link href="/admin" className="btn-ghost">Admin</Link>
            )}
            {user?.role === "student" && (
              <>
                <Link href="/dashboard" className="btn-ghost">Dashboard</Link>
                <Link href="/skills" className="btn-ghost">Skills</Link>
                <Link href="/demand" className="btn-ghost">Market Demand</Link>
                <Link href="/gap" className="btn-ghost">Skill Gaps</Link>
                <Link href="/roadmap" className="btn-ghost">Roadmap</Link>
                <Link href="/projects" className="btn-ghost">Projects</Link>
                <Link href="/profile" className="btn-ghost">Profile</Link>
              </>
            )}
          </nav>

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <div className="hidden sm:block text-right">
                  <p className="text-sm font-medium text-navy-900 leading-tight">{user.full_name}</p>
                  <p className="text-xs text-navy-500">{user.role}</p>
                </div>
                <button
                  onClick={logout}
                  className="btn-ghost text-red-600 hover:bg-red-50 hover:text-red-700"
                >
                  Sign out
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/login" className="btn-ghost">Sign in</Link>
                <Link href="/register" className="btn-primary text-xs px-4 py-2">Get started</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
