"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Profile, Demand, SkillGapList, Roadmap, DemandSkill, SkillGap, Skill,
} from "@/lib/types";
import ProgressRing from "@/components/ui/ProgressRing";
import StatCard from "@/components/ui/StatCard";
import SkillPill from "@/components/ui/SkillPill";
import {
  Target, MapPin, BookOpen, TrendingUp, AlertTriangle, Trophy, ArrowRight,
  Lightbulb, Clock, CircleCheck, Check,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { cn, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [demand, setDemand] = useState<Demand | null>(null);
  const [gaps, setGaps] = useState<SkillGapList | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/students/profile").catch(() => ({ data: null })),
      api.get("/demand").catch(() => ({ data: null })),
      api.get("/skill-gap").catch(() => ({ data: null })),
      api.get("/roadmap").catch(() => ({ data: null })),
    ]).then(([p, d, g, r]) => {
      setProfile(p.data);
      setDemand(d.data);
      setGaps(g.data);
      setRoadmap(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading dashboard…</div>;

  const region = profile?.preferred_region;
  const role = profile?.target_role;

  // Prepare chart data
  const demandChartData = (demand?.skills || []).slice(0, 8).map((s) => ({
    name: s.skill.name,
    value: s.demand_percent,
    confidence: s.confidence,
  }));

  const gapChartData = [
    { name: "Matched", count: gaps?.gaps.filter((g) => g.status === "matched").length || 0, color: "#10b981" },
    { name: "Partial", count: gaps?.gaps.filter((g) => g.status === "partial").length || 0, color: "#f59e0b" },
    { name: "Missing", count: gaps?.gaps.filter((g) => g.status === "missing").length || 0, color: "#ef4444" },
  ].filter((d) => d.count > 0 || true);

  const yourSkills = (gaps?.gaps || []).filter((g) => g.status === "matched" || g.status === "partial").slice(0, 6);
  const missingSkills = (gaps?.gaps || []).filter((g) => g.status === "missing").slice(0, 6);
  const topPriority = (gaps?.gaps || []).find((g) => g.status === "missing") || null;

  const readiness = gaps?.readiness_percent ?? 0;
  const coverage = gaps?.demand_coverage_percent ?? 0;

  return (
    <div>
      {/* Header strip */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
              Hello, {user?.full_name || "Student"}
              <span className="text-sm font-normal text-navy-500">· Student</span>
            </h1>
            <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-navy-600">
              {role && <span className="flex items-center gap-1"><Target className="w-3.5 h-3.5 text-accent-400" /> {role.name}</span>}
              {region && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5 text-accent-400" /> {region.name}</span>}
            </div>
          </div>
          <Link href="/roadmap" className="btn-primary text-sm flex items-center gap-2 self-start">
            View roadmap <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Badges */}
      {(demand?.is_demo || gaps) && (
        <div className="flex flex-wrap items-center gap-3 mb-6">
          {demand?.is_demo && (
            <span className="badge-demo"><span className="w-1.5 h-1.5 rounded-full bg-navy-500" /> DEMO DATA</span>
          )}
          <span className="text-sm text-navy-600">Readiness: <strong className="text-navy-900">{formatPercent(readiness, 0)}</strong></span>
          <span className="text-sm text-navy-600">Demand coverage: <strong className="text-navy-900">{formatPercent(coverage, 0)}</strong></span>
        </div>
      )}

      {/* Readiness ring + stats */}
      <div className="card-grid mb-6">
        <div className="card flex flex-col items-center justify-center">
          <ProgressRing value={readiness} max={100} size={140} strokeWidth={12} color="#1d4173" label={formatPercent(readiness, 0)} sublabel="job-ready estimate" />
          <p className="text-xs text-navy-500 mt-3 text-center">
            {readiness >= 70 ? "Strong foundation" : readiness >= 40 ? "Getting there" : "Early stage"}
          </p>
        </div>
        <StatCard title="Market demand skills" value={demand?.total_jobs || 0} subtitle={`${demand?.confidence || "unknown"} confidence · ${demand?.time_window || "all"}`} icon={<TrendingUp className="w-5 h-5" />} accent />
        <StatCard title="Top priority gap" value={topPriority ? topPriority.skill?.name || "—" : "—"} subtitle={topPriority ? `${formatPercent(topPriority.priority_score, 0)} priority` : "None identified"} icon={<AlertTriangle className="w-5 h-5 text-red-500" />} />
        <StatCard title="Roadmap weeks" value={roadmap?.items.length || 0} subtitle={roadmap?.items.some((i) => i.status === "completed") ? `${roadmap.items.filter((i) => i.status === "completed").length} done` : "Not started"} icon={<BookOpen className="w-5 h-5" />} />
      </div>

      {/* Charts row */}
      <div className="card-grid-2 mb-6">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Top regional skills</h2>
            {demand?.is_demo && <span className="badge-demo">DEMO</span>}
          </div>
          {demandChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={demandChartData} layout="vertical" margin={{ left: 20, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6edf6" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} stroke="#94a3b8" fontSize={11} />
                <YAxis type="category" dataKey="name" width={100} stroke="#94a3b8" fontSize={11} />
                <Tooltip
                  formatter={(v: number) => [`${v.toFixed(0)}%`, "Demand %"]}
                  labelStyle={{ color: "#0f2440" }}
                  contentStyle={{ backgroundColor: "#fff", border: "1px solid #e6edf6", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="value" fill="#1d4173" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-navy-500 text-sm">No demand data yet</div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Your skill status</h2>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={gapChartData}
                innerRadius={55}
                outerRadius={80}
                paddingAngle={3}
                dataKey="count"
                nameKey="name"
              >
                {gapChartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} stroke="none" />
                ))}
              </Pie>
              <Tooltip formatter={(v: number) => [v, "skills"]} contentStyle={{ backgroundColor: "#fff", border: "1px solid #e6edf6", borderRadius: 8, fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2 text-xs">
            {gapChartData.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="text-navy-600">{d.name} ({d.count})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Skill cards: yours + missing */}
      <div className="card-grid mb-6">
        <div className="card md:col-span-2">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><CircleCheck className="w-4 h-4 text-emerald-500" /> Your skills</h2>
            <span className="text-sm text-navy-500">{yourSkills.length} matched/partial</span>
          </div>
          {yourSkills.length === 0 ? (
            <div className="py-6 text-center text-navy-500 text-sm">No skills added yet. Add skills or upload a resume to get started.</div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {yourSkills.map((g) => (
                <SkillPill key={g.id} skill={g.skill!} status={g.status as any} level={g.student_level as any} />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card-grid">
        <div className="card md:col-span-1">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-red-500" /> Missing / gaps</h2>
            <span className="text-sm text-navy-500">{missingSkills.length} missing</span>
          </div>
          {missingSkills.length === 0 ? (
            <div className="py-6 text-center text-emerald-600 text-sm">No missing skills — great start!</div>
          ) : (
            <div className="space-y-2">
              {missingSkills.map((g) => (
                <div key={g.id} className="flex items-start justify-between gap-2 p-2 rounded-xl hover:bg-navy-100 transition">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-navy-900 text-sm">{g.skill?.name}</span>
                      <span className="skill-pill skill-pill-missing text-xs">missing</span>
                    </div>
                    {g.priority_reason && (
                      <p className="text-xs text-navy-600 mt-1 line-clamp-2">{g.priority_reason}</p>
                    )}
                  </div>
                  <div className="shrink-0 text-right">
                    <span className="text-xs font-semibold text-navy-700">{formatPercent(g.priority_score, 0)}</span>
                    <span className="text-[10px] text-navy-500 block">priority</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card md:col-span-1">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><Lightbulb className="w-4 h-4 text-accent-400" /> Top priority</h2>
          </div>
          {topPriority ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-navy-900">{topPriority.skill?.name}</p>
                  <p className="text-sm text-navy-600">{topPriority.evidence?.evidence || "See gap details for full reasoning."}</p>
                </div>
                <span className="text-2xl font-bold text-accent-400">{formatPercent(topPriority.priority_score, 0)}</span>
              </div>
              <div className="rounded-xl bg-navy-100 p-3 text-xs text-navy-700">
                <p className="font-medium text-navy-900 mb-1">Why this skill?</p>
                <p>{topPriority.priority_reason || "See explanation in skill gap view."}</p>
              </div>
              <Link href="/gap" className="btn-ghost text-sm flex items-center gap-1 justify-end">
                See full gap analysis <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <div className="py-6 text-center text-navy-500 text-sm">No missing skills — focus on building proof for what you have.</div>
          )}
        </div>
      </div>

      {/* Roadmap progress strip */}
      {roadmap && roadmap.items.length > 0 && (
        <div className="card mt-6">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2"><Clock className="w-4 h-4 text-navy-500" /> Your roadmap progress</h2>
            <span className="text-sm text-navy-500">{roadmap.items.length} weeks</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {roadmap.items.map((item) => (
              <div
                key={item.id}
                className={cn(
                  "rounded-xl border px-3 py-2 text-sm flex items-center gap-2 transition",
                  item.status === "completed" && "border-emerald-200 bg-emerald-50 text-emerald-700",
                  item.status === "in_progress" && "border-accent-400 bg-accent-50/30 text-accent-700",
                  item.status === "pending" && "border-surface-line text-navy-600",
                )}
              >
                <span className="font-medium">W{item.week_number}</span>
                <span className="truncate">{item.title}</span>
                {item.status === "completed" && <Check className="w-3.5 h-3.5 shrink-0" />}
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-navy-500">
            <span>
              {roadmap.items.filter((i) => i.status === "completed").length} of {roadmap.items.length} weeks complete
            </span>
            <Link href="/roadmap" className="text-accent-500 font-medium hover:underline">View full roadmap →</Link>
          </div>
        </div>
      )}
    </div>
  );
}
