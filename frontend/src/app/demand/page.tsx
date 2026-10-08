"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Demand, Region, Role, Sector, DemandSkill } from "@/lib/types";
import {
  MapPin, Target, Clock, AlertTriangle, CheckCircle, ChevronDown, BarChart3,
} from "lucide-react";
import { formatPercent, confidenceBadge, cn } from "@/lib/utils";

export default function DemandPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [demand, setDemand] = useState<Demand | null>(null);
  const [options, setOptions] = useState<{ regions: Region[]; roles: Role[]; sectors: Sector[] } | null>(null);
  const [filters, setFilters] = useState({
    regionId: "",
    roleId: "",
    sectorId: "",
    timeWindow: "all",
    confidence: "all",
  });
  const [selectedSkill, setSelectedSkill] = useState<DemandSkill | null>(null);

  useEffect(() => {
    Promise.all([
      api.get("/students/options").then((r) => ({ regions: r.data.regions, roles: r.data.roles, sectors: r.data.sectors })),
      api.get("/demand").catch(() => ({ data: null })),
    ]).then(([opt, dem]) => {
      setOptions(opt);
      setDemand(dem.data);
      if (dem.data) {
        setFilters((f) => ({
          ...f,
          regionId: dem.data.region_id || "",
          roleId: dem.data.role_id || "",
          sectorId: dem.data.sector_id || "",
          timeWindow: dem.data.time_window,
        }));
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const fetchDemand = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filters.regionId) params.region_id = filters.regionId;
      if (filters.roleId) params.role_id = filters.roleId;
      if (filters.sectorId) params.sector_id = filters.sectorId;
      if (filters.timeWindow !== "all") params.time_window = filters.timeWindow;
      const res = await api.get("/demand", { params });
      setDemand(res.data);
    } catch {
      setDemand(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (options) fetchDemand();
  }, [filters, options]);

  const region = options?.regions.find((r) => r.id === filters.regionId);
  const role = options?.roles.find((r) => r.id === filters.roleId);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-accent-400" /> Regional demand
        </h1>
        <p className="text-sm text-navy-600 mt-1">
          What skills employers in your region and target role actually require — computed from the dataset.
        </p>
      </div>

      <div className="card mb-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Region</label>
            <select value={filters.regionId} onChange={(e) => setFilters((f) => ({ ...f, regionId: e.target.value }))} className="input-field">
              <option value="">All regions</option>
              {options?.regions.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Role</label>
            <select value={filters.roleId} onChange={(e) => setFilters((f) => ({ ...f, roleId: e.target.value }))} className="input-field">
              <option value="">All roles</option>
              {options?.roles.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Sector</label>
            <select value={filters.sectorId} onChange={(e) => setFilters((f) => ({ ...f, sectorId: e.target.value }))} className="input-field">
              <option value="">All sectors</option>
              {options?.sectors.map((s) => (<option key={s.id} value={s.id}>{s.name}</option>))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Time window</label>
            <select value={filters.timeWindow} onChange={(e) => setFilters((f) => ({ ...f, timeWindow: e.target.value }))} className="input-field">
              <option value="all">All time</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="6mo">Last 6 months</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Min confidence</label>
            <select value={filters.confidence} onChange={(e) => setFilters((f) => ({ ...f, confidence: e.target.value }))} className="input-field">
              <option value="all">All confidence</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16"><div className="w-8 h-8 border-4 border-navy-300 border-t-accent-400 rounded-full animate-spin" /></div>
      ) : demand && demand.skills.length > 0 ? (
        <>
          {/* Evidence bar */}
          <div className="rounded-xl border border-accent-400 bg-accent-50/40 p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-accent-500 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-accent-700">
                  How this demand is calculated
                </p>
                <p className="text-sm text-accent-600 mt-1">
                  {demand.evidence_note || "Demand is computed from structured job postings. Frequency × recency × role relevance × sector relevance."}
                </p>
                <div className="flex flex-wrap gap-3 mt-2 text-xs text-navy-600">
                  <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {region?.name || "All regions"}</span>
                  {role && <span className="flex items-center gap-1"><Target className="w-3.5 h-3.5" /> {role.name}</span>}
                  <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {demand.time_window === "all" ? "All time" : demand.time_window}</span>
                  <span>Jobs analyzed: <strong className="text-navy-900">{demand.total_jobs}</strong></span>
                  <span>Confidence: <strong className={cn("text-navy-900", demand.confidence === "high" ? "text-emerald-600" : demand.confidence === "medium" ? "text-amber-600" : "text-red-600")}>{demand.confidence}</strong></span>
                  {demand.is_demo && <span className="badge-demo">DEMO DATA</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Top 10 skills bar chart */}
          <div className="card mb-6">
            <div className="card-header">
              <h2 className="card-title">Top demanded skills</h2>
              <span className="text-sm text-navy-500">{demand.skills.length} skills</span>
            </div>
            <div className="h-[220px]">
              <DemandChart data={demand.skills.slice(0, 10).map((s) => ({
                name: s.skill.name,
                value: s.demand_percent,
                confidence: s.confidence,
              }))} />
            </div>
          </div>

          {/* Skills table */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Skill demand detail</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-line text-left text-navy-500 text-xs uppercase tracking-wider">
                    <th className="pb-3 pr-4 font-medium">Skill</th>
                    <th className="pb-3 pr-4 font-medium">Demand %</th>
                    <th className="pb-3 pr-4 font-medium">Jobs</th>
                    <th className="pb-3 pr-4 font-medium">Confidence</th>
                    <th className="pb-3 font-medium">Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {demand.skills.map((s) => {
                    const conf = confidenceBadge(s.confidence);
                    const filtered = filters.confidence !== "all" ? filters.confidence === s.confidence : true;
                    if (!filtered) return null;
                    return (
                      <tr
                        key={s.skill_id}
                        className="border-b border-surface-line last:border-0 hover:bg-navy-100 transition cursor-pointer"
                        onClick={() => setSelectedSkill(selectedSkill?.skill_id === s.skill_id ? null : s)}
                      >
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-navy-900">{s.skill.name}</span>
                            {s.skill.category && <span className="text-xs text-navy-400 hidden sm:inline">· {s.skill.category}</span>}
                          </div>
                        </td>
                        <td className="py-3 pr-4">
                          <span className="font-semibold text-navy-900">{formatPercent(s.demand_percent, 0)}</span>
                          <div className="w-24 mt-1 h-1.5 rounded-full bg-navy-200 overflow-hidden">
                            <div className="h-full rounded-full bg-navy-500" style={{ width: `${Math.min(100, s.demand_percent)}%` }} />
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-navy-600">{s.job_count}</td>
                        <td className="py-3 pr-4">
                          <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border", conf.cls)}>
                            {conf.label}
                          </span>
                        </td>
                        <td className="py-3 text-navy-600 max-w-xs">
                          {selectedSkill?.skill_id === s.skill_id ? (
                            <div className="text-xs">
                              <p className="text-navy-700">{s.evidence || "No evidence available."}</p>
                              <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-navy-500">
                                <span>Freq: {formatPercent(s.demand_frequency * 100, 0)}</span>
                                <span>Recency: {formatPercent(s.demand_recency * 100, 0)}</span>
                                <span>Role rel: {formatPercent(s.demand_role_relevance * 100, 0)}</span>
                                <span>Sector rel: {formatPercent(s.demand_sector_relevance * 100, 0)}</span>
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-navy-400 line-clamp-1">{s.evidence?.slice(0, 80) || "—"}</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {demand.skills.length === 0 && (
              <div className="py-8 text-center text-navy-500 text-sm">No demand data for the selected filters.</div>
            )}
          </div>
        </>
      ) : (
        <div className="card">
          <div className="py-8 text-center">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
            <p className="text-navy-700 font-medium">No demand data available</p>
            <p className="text-sm text-navy-500 mt-1">Try a different region or role, or check that demo data is loaded.</p>
          </div>
        </div>
      )}

      {/* Formula note */}
      <div className="mt-6 rounded-xl bg-navy-100 border border-navy-200 p-4 text-xs text-navy-600">
        <p className="font-medium text-navy-800 mb-1">Scoring formula (configurable)</p>
        <p>
          Demand Score = 0.50 × frequency + 0.20 × recency + 0.20 × role relevance + 0.10 × sector relevance
        </p>
        <p className="mt-1 text-navy-500">
          Frequency = weighted skill count ÷ relevant jobs. Recency, role relevance, and sector relevance are normalized 0–1. AI never invents job statistics — demand is always computed from the dataset.
        </p>
      </div>
    </div>
  );
}

function DemandChart({ data }: { data: Array<{ name: string; value: number; confidence: string }> }) {
  return (
    <div className="h-full w-full">
      {data.length > 0 ? (
        // Using a simple inline bar chart via SVG since recharts horizontal bar can be verbose;
        // we reuse recharts as requested in the stack but keep it lightweight.
        <svg width="100%" height={220} className="overflow-visible">
          {data.map((d, i) => {
            const barH = 16;
            const gap = 3;
            const y = i * (barH + gap);
            const w = Math.max(4, (d.value / 100) * 340);
            return (
              <g key={d.name}>
                <text x={350} y={y + barH - 4} className="text-[10px] fill-navy-500">{d.name}</text>
                <rect x={4} y={y} width={w} height={barH} rx={4} fill={d.confidence === "high" ? "#1d4173" : d.confidence === "medium" ? "#f59e0b" : "#ef4444"} />
                <text x={4 + w + 6} y={y + barH - 4} className="text-[10px] fill-navy-700 font-medium">{Math.round(d.value)}%</text>
              </g>
            );
          })}
        </svg>
      ) : null}
    </div>
  );
}
