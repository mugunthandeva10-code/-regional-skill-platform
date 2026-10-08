"use client";

import React from "react";
import { Skill } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SkillPillProps {
  skill: Skill;
  status?: "matched" | "partial" | "missing" | "neutral";
  level?: string;
  selected?: boolean;
  onClick?: () => void;
  size?: "sm" | "md";
}

const statusClass = {
  matched: "skill-pill-matched",
  partial: "skill-pill-partial",
  missing: "skill-pill-missing",
  neutral: "bg-navy-100 text-navy-800 border-navy-200",
};

const levelColor: Record<string, string> = {
  advanced: "bg-navy-600 text-white",
  intermediate: "bg-blue-100 text-navy-700",
  beginner: "bg-amber-100 text-amber-700",
  none: "bg-surface text-navy-500 border-surface-line",
};

export default function SkillPill({
  skill,
  status = "neutral",
  level,
  selected = false,
  onClick,
  size = "md",
}: SkillPillProps) {
  const base = "inline-flex items-center gap-1.5 rounded-full font-medium border transition";
  const cls = cn(
    base,
    statusClass[status],
    selected && "ring-2 ring-accent-400 border-accent-400",
    size === "sm" && "px-2 py-0.5 text-xs",
    size === "md" && "px-3 py-1 text-sm",
    onClick && "cursor-pointer hover:brightness-95",
  );

  return (
    <div className={cls} onClick={onClick} role={onClick ? "button" : undefined} tabIndex={onClick ? 0 : undefined}>
      {status !== "neutral" && (
        <span className="text-base leading-none">
          {status === "matched" ? "✓" : status === "partial" ? "⚠" : "✗"}
        </span>
      )}
      <span>{skill.name}</span>
      {level && status !== "neutral" && (
        <span className={cn("text-[10px] font-semibold uppercase tracking-wide", levelColor[level])}>
          {level}
        </span>
      )}
    </div>
  );
}
