"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AdminStatistics, DataQuality } from "@/lib/types";
import StatCard from "@/components/ui/StatCard";
import {
  Users, Briefcase, Hash, MapPin, TrendingUp, Target, AlertTriangle,
  Download, Upload, Plus, BarChart3, PieChart,
} from "lucide-react";
import { formatNumber } from "@/lib/utils";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RCpie, Pie, Cell } from "recharts";

export default function AdminPage() {
  const router = useRouter();
  const { user, isAdmin } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AdminStatistics | null>(null);
  const [dq, setDq] = useState<DataQuality | null>(null);

  useEffect(() => {
    if (!isAdmin) {
      router.push("/");
      return;
    }
    Promise.all([
      api.get("/admin/statistics").catch(() => ({ data: null })),
      api.get("/admin/data-quality").catch(() => ({ data: null })),
    ]).then(([s, d]) => {
      setStats(s.data);
      setDq(d.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [isAdmin, router]);

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading admin…</div>;
  if (!isAdmin) return null;

  const rolesChartData = (stats?.most_selected_roles || []).map((r) => ({
    name: r.role_name,
    value: r.count,
  }));

  const topSkillsData = (stats?.top_demanded_skills || []).slice(0, 8).map((s) => ({
    name: s.skill.name,
    value: s.demand_percent,
    confidence: s.confidence,
  }));

  const colors = ["#1d4173", "#2a5696", "#4a7ab8", "#7fa0d4", "#a9c2e6", "#ff8a5c", "#ffb38a", "#ffd9c4"];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-accent-400" /> Admin dashboard
        </h1>
        <p className="text-sm text-navy-600 mt-1">Manage regions, roles, skills, jobs, and data quality.</p>
      </div>

      <div className="card-grid mb-6">
        <StatCard title="Total students" value={stats?.total_students ?? 0} icon={<Users className="w-5 h-5" />} accent />
        <StatCard title="Total jobs" value={stats?.total_jobs ?? 0} subtitle={dq?.is_demo_data ? "Includes demo data" : ""} icon={<Briefcase className="w-5 h-5" />} />
        <StatCard title="Total skills" value={stats?.total_skills ?? 0} icon={<Hash className="w-5 h-5" />} />
        <StatCard title="Regions" value={stats?.total_regions ?? 0} icon={<MapPin className="w-5 h-5" />} />
        <StatCard title="Roles" value={stats?.total_roles ?? 0} icon={<Target className="w-5 h-5" />} />
        <StatCard title="Sectors" value={stats?.total_sectors ?? 0} icon={<PieChart className="w-5 h-5" />} />
        <StatCard title="Avg gaps / student" value={stats?.average_skill_gaps ?? 0} subtitle="Missing + partial" icon={<AlertTriangle className="w-5 h-5 text-red-500" />} />
        <StatCard title="Data quality" value={dq?.confidence_level || "unknown"} subtitle={dq?.percentage_with_extracted_skills ? `${dq.percentage_with_extracted_skills}% jobs with skills` : ""} icon={<TrendingUp className="w-5 h-5" />} />
      </div>

      <div className="card-grid-2 mb-6">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Jobs by role</h2>
          </div>
          {rolesChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={rolesChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6edf6" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #e6edf6", borderRadius: 8 }} />
                <Bar dataKey="value" fill="#1d4173" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[240px] flex items-center justify-center text-navy-500 text-sm">No role data</div>
          )}
        </div>
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Top demanded skills</h2>
          </div>
          {topSkillsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={topSkillsData} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6edf6" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip formatter={(v: number) => [`${v.toFixed(0)}%`, "Demand %"]} contentStyle={{ backgroundColor: "#fff", border: "1px solid #e6edf6", borderRadius: 8 }} />
                <Bar dataKey="value" fill="#ff6b2c" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[240px] flex items-center justify-center text-navy-500 text-sm">No demand data</div>
          )}
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h2 className="card-title">Data quality</h2>
          {dq?.is_demo_data && <span className="badge-demo">DEMO DATA</span>}
        </div>
        {dq && (
          <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">Jobs analyzed</p>
              <p className="text-2xl font-bold text-navy-900">{formatNumber(dq.jobs_analyzed)}</p>
            </div>
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">With skill extraction</p>
              <p className="text-2xl font-bold text-navy-900">{formatNumber(dq.jobs_with_skill_extraction)}</p>
              <p className="text-xs text-navy-600 mt-1">{dq.percentage_with_extracted_skills}% of jobs</p>
            </div>
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">Unique skills</p>
              <p className="text-2xl font-bold text-navy-900">{formatNumber(dq.unique_skills)}</p>
            </div>
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">Confidence</p>
              <p className="text-2xl font-bold text-navy-900">{dq.confidence_level}</p>
              <p className="text-xs text-navy-600 mt-1">{dq.is_demo_data ? "Demo dataset" : "Live dataset"}</p>
            </div>
          </div>
          {dq.note && <p className="text-xs text-navy-500 mt-3">{dq.note}</p>}
          </>
        )}
      </div>

      <div className="card-grid">
        <div className="card flex items-center gap-4 md:col-span-2">
          <div className="flex-1">
            <h3 className="font-semibold text-navy-900">Import jobs (CSV)</h3>
            <p className="text-sm text-navy-600 mt-1">CSV columns: job_title, company, city, state, sector, description, posted_date, source, source_url.</p>
            <label className="btn-secondary text-sm mt-3 cursor-pointer inline-flex items-center gap-2">
              <Upload className="w-4 h-4" /> Import CSV
              <input type="file" accept=".csv" className="hidden" id="csv-import" onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                setLoading(true);
                try {
                  const form = new FormData();
                  form.append("file", file);
                  const res = await api.post("/admin/import-jobs", form, { headers: { "Content-Type": "multipart/form-data" } });
                  alert(`Imported ${res.data.imported}, skipped ${res.data.skipped}`);
                  refresh();
                } catch (err: any) {
                  alert(err?.response?.data?.detail || "Import failed");
                } finally {
                  setLoading(false);
                }
                e.target.value = "";
              }} />
            </label>
          </div>
          <div className="hidden sm:block text-xs text-navy-500">
            <p className="font-medium text-navy-700">Tip</p>
            <p className="mt-1">Demo data is already seeded. Use CSV import to add real or curated data.</p>
          </div>
        </div>

        <div className="card flex items-center gap-4 md:col-span-2">
          <div className="flex-1">
            <h3 className="font-semibold text-navy-900">Reseed demo dataset</h3>
            <p className="text-sm text-navy-600 mt-1">Re-seed regions, roles, sectors, skills, and demo jobs.</p>
            <button
              onClick={async () => {
                if (!confirm("This will re-seed demo data. Continue?")) return;
                setLoading(true);
                try {
                  await api.post("/admin/seed-demo");
                  alert("Demo data reseeded.");
                  refresh();
                } catch (err: any) {
                  alert(err?.response?.data?.detail || "Seed failed");
                } finally {
                  setLoading(false);
                }
              }}
              className="btn-secondary text-sm mt-3"
            >
              <Hash className="w-4 h-4" /> Reseed demo
            </button>
          </div>
          <div className="hidden sm:block text-xs text-navy-500">
            <p className="font-medium text-navy-700">Note</p>
            <p className="mt-1">Always label demo data clearly. Never present it as live market data.</p>
          </div>
        </div>
      </div>

      <div className="mt-6 text-center text-xs text-navy-500">
        Admin access only. Use rate limiting, input validation, and secure file uploads in production.
      </div>
    </div>
  );
}

async function refresh() {
  const [s, d] = await Promise.all([
    api.get("/admin/statistics"),
    api.get("/admin/data-quality"),
  ]);
  // caller re-renders via state
}
