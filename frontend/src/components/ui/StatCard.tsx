"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  accent?: boolean;
  hover?: boolean;
  className?: string;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  accent = false,
  hover = false,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "card",
        accent && "border-accent-400 bg-accent-50/40",
        hover && "transition hover:border-navy-200 hover:shadow-md",
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-navy-500 uppercase tracking-wider">{title}</p>
          <p className="text-3xl font-bold text-navy-900 mt-1">{value}</p>
          {subtitle && <p className="text-sm text-navy-600 mt-1">{subtitle}</p>}
        </div>
        {icon && <div className="text-navy-400">{icon}</div>}
      </div>
    </div>
  );
}
