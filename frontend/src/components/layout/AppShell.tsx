"use client";

import React from "react";
import Header from "./Header";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-navy-100">
      <Header />
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="border-t border-surface-line bg-white/50 mt-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-navy-500">
            <p>
              Regional Skill Intelligence Platform — Demo / MVP.
            </p>
            <p className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-accent-400" />
              Demand is computed from curated job datasets, not live market data.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
