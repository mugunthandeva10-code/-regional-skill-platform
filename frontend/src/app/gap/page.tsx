"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { SkillGapList, SkillGap, DemandSkill, Skill } from "@/lib/types";
import SkillPill from "@/components/ui/SkillPill";
import StatCard from "@/components/ui/StatCard";
import {
  TrendingUp, AlertTriangle, CheckCircle, Info, Lightbulb, Target,
} from "lucide-react";
import { formatPercent, cn } from "@/lib/utils";

export default function GapPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [gaps, setGaps] = useState<SkillGapList | null>(null);
  const [selected, setSelected] = useState<SkillGap | null>(null);

  useEffect(() => {
    api.get("/skill-gap").then((res) => {
      setGaps(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const matched = gaps?.gaps.filter((g) => g.status === "matched") || [];
  const partial = gaps?.gaps.filter((g) => g.status === "partial") || [];
  const missing = gaps?.gaps.filter((g) => g.status === "missing") || [];
  const sortedByPriority = [...(gaps?.gaps || [])].sort((a, b) => b.priority_score - a.priority_score);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-accent-400" /> Skill gaps
        </h1>
        <p className="text-sm text-navy-600 mt-1">
          Your skills vs what the market needs — ranked by priority.
        </p>
      </div>

      <div className="card-grid mb-6">
        <StatCard title="Readiness" value={formatPercent(gaps?.readiness_percent ?? 0, 0)} subtitle="Matched ÷ demand skills" icon={<TrendingUp className="w-5 h-5 text-emerald-500" />} accent />
        <StatCard title="Demand coverage" value={formatPercent(gaps?.demand_coverage_percent ?? 0, 0)} subtitle="Skills at/above target" icon={<CheckCircle className="w-5 h-5 text-navy-500" />} />
        <StatCard title="Matched" value={matched.length} subtitle="At or above target level" icon={<CheckCircle className="w-5 h-5 text-emerald-500" />} />
        <StatCard title="Priority gaps" value={missing.length} subtitle="Need attention" icon={<AlertTriangle className="w-5 h-5 text-red-500" />} />
      </div>

      {/* Matched skills */}
      {matched.length > 0 && (
        <div className="card mb-6">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><CheckCircle className="w-4 h-4 text-emerald-500" /> Your skills (matched)</h2>
            <span className="text-sm text-navy-500">{matched.length}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {matched.map((g) => (
              <SkillPill key={g.id} skill={g.skill!} status="matched" level={g.student_level as any} />
            ))}
          </div>
        </div>
      )}

      {/* Partial skills */}
      {partial.length > 0 && (
        <div className="card mb-6">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><Info className="w-4 h-4 text-amber-500" /> Partial</h2>
            <span className="text-sm text-navy-500">{partial.length}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {partial.map((g) => (
              <SkillPill key={g.id} skill={g.skill!} status="partial" level={g.student_level as any} />
            ))}
          </div>
          <p className="text-xs text-navy-500 mt-2">You have some exposure but are not yet at target level.</p>
        </div>
      )}

      {/* Missing skills: priority list */}
      {missing.length > 0 && (
        <div className="card mb-6 md:col-span-2">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><Lightbulb className="w-4 h-4 text-accent-400" /> Missing skills — priority order</h2>
            <span className="text-sm text-navy-500">{missing.length}</span>
          </div>
          <div className="space-y-2">
            {sortedByPriority
              .filter((g) => g.status === "missing")
              .map((g, idx) => (
                <div
                  key={g.id}
                  className={cn(
                    "rounded-xl border p-4 transition cursor-pointer hover:border-navy-200 hover:bg-navy-100",
                    selected?.id === g.id ? "border-accent-400 bg-accent-50/30" : "border-surface-line",
                  )}
                  onClick={() => setSelected(selected?.id === g.id ? null : g)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-navy-100 text-xs font-bold text-navy-700 shrink-0">{idx + 1}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-navy-900">{g.skill?.name}</span>
                          <span className="skill-pill skill-pill-missing text-xs">missing</span>
                          {g.evidence && <span className={cn("text-xs", g.evidence.confidence === "high" ? "text-emerald-600" : g.evidence.confidence === "medium" ? "text-amber-600" : "text-red-600")}>{g.evidence.confidence} confidence</span>}
                        </div>
                        {g.market_demand > 0 && (
                          <p className="text-xs text-navy-600 mt-0.5">
                            {formatPercent(g.market_demand * 100, 0)} of relevant jobs require this · {g.evidence?.job_count || 0} jobs
                          </p>
                        )}
                        <div className="mt-2 w-full h-2 rounded-full bg-navy-200 overflow-hidden">
                          <div className="h-full rounded-full bg-accent-400" style={{ width: `${Math.min(100, g.priority_score)}%` }} />
                        </div>
                        <div className="flex justify-between mt-1 text-[10px] text-navy-500">
                          <span>Priority</span>
                          <span className="font-semibold text-navy-900">{formatPercent(g.priority_score, 0)} / 100</span>
                        </div>
                      </div>
                    </div>
                    <button className="btn-ghost text-xs shrink-0">View details</button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Detail panel */}
      {selected && (
        <div className="card mb-6 border-accent-400 bg-accent-50/30">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><Target className="w-4 h-4 text-accent-400" /> {selected.skill?.name}</h2>
            <button onClick={() => setSelected(null)} className="btn-ghost text-xs">Close</button>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-navy-900">Why it matters</p>
              <p className="text-sm text-navy-600 mt-1">{selected.priority_reason || "See demand evidence below."}</p>
              {selected.evidence && (
                <div className="mt-3 rounded-xl bg-navy-100 p-3 text-xs text-navy-700">
                  <p className="font-medium text-navy-900">Market evidence</p>
                  <p className="mt-1 text-navy-600">{selected.evidence.evidence || "No evidence available."}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className="text-navy-500">Demand: <strong className="text-navy-900">{formatPercent(selected.evidence.demand_percent, 0)}</strong></span>
                    <span className="text-navy-500">Jobs: <strong className="text-navy-900">{selected.evidence.job_count}</strong></span>
                    <span className="text-navy-500">Confidence: <strong className="text-navy-900">{selected.evidence.confidence}</strong></span>
                  </div>
                </div>
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-navy-900">Your status vs market</p>
              <div className="mt-2 space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-navy-600">Your level</span><span className="font-medium text-navy-900 capitalize">{selected.student_level}</span></div>
                <div className="flex justify-between"><span className="text-navy-600">Market demand</span><span className="font-medium text-navy-900">{formatPercent(selected.market_demand * 100, 0)}</span></div>
                <div className="flex justify-between"><span className="text-navy-600">Status</span><span className="font-medium text-red-600 capitalize">{selected.status}</span></div>
                <div className="flex justify-between"><span className="text-navy-600">Priority score</span><span className="font-medium text-accent-500">{formatPercent(selected.priority_score, 0)} / 100</span></div>
              </div>
              <div className="mt-3 rounded-xl bg-emerald-50 p-3 text-xs text-emerald-700">
                <p className="font-medium">Recommended action</p>
                <p className="mt-1">Add to your roadmap and build a small project to prove it. See the roadmap page for a 6-week plan.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {missing.length === 0 && matched.length > 0 && (
        <div className="card">
          <div className="py-8 text-center">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
            <p className="text-navy-700 font-medium">No missing skills</p>
            <p className="text-sm text-navy-500 mt-1">Focus on building project proof for the skills you already have.</p>
          </div>
        </div>
      )}

      {gaps && gaps.gaps.length === 0 && (
        <div className="card">
          <div className="py-8 text-center">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
            <p className="text-navy-700 font-medium">No skill gaps yet</p>
            <p className="text-sm text-navy-500 mt-1">Add skills or upload a resume on your profile page to compare against market demand.</p>
          </div>
        </div>
      )}
    </div>
  );
}
