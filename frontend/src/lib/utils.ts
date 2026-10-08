export type ClassValue = string | number | null | undefined | false | ClassValue[];

/** Join class names, skipping falsy values. */
export function cn(...inputs: ClassValue[]): string {
  const out: string[] = [];
  const walk = (v: ClassValue): void => {
    if (!v && v !== 0) return;
    if (Array.isArray(v)) {
      v.forEach(walk);
      return;
    }
    out.push(String(v));
  };
  inputs.forEach(walk);
  return out.join(" ");
}

export function formatPercent(value: number, decimals = 0) {
  return `${(value).toFixed(decimals)}%`;
}

export function formatNumber(n: number) {
  return n.toLocaleString();
}

export function skillStatusBadge(status: string) {
  switch (status) {
    case "matched":
      return { label: "Matched", cls: "skill-pill-matched" };
    case "partial":
      return { label: "Partial", cls: "skill-pill-partial" };
    case "missing":
      return { label: "Missing", cls: "skill-pill-missing" };
    default:
      return { label: status, cls: "skill-pill" };
  }
}

export function confidenceBadge(confidence: string) {
  const map: Record<string, { label: string; cls: string }> = {
    high: { label: "High", cls: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    medium: { label: "Medium", cls: "bg-amber-50 text-amber-700 border-amber-200" },
    low: { label: "Low", cls: "bg-red-50 text-red-700 border-red-200" },
  };
  return map[confidence] || map.low;
}
