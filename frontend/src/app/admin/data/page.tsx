"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { DataQuality, Region, Role, Sector, Skill } from "@/lib/types";
import {
  Download, Upload, Hash, RefreshCw, Database, BarChart3,
} from "lucide-react";

export default function AdminDataPage() {
  const router = useRouter();
  const { isAdmin } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dq, setDq] = useState<DataQuality | null>(null);
  const [regions, setRegions] = useState<Region[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);

  useEffect(() => {
    if (!isAdmin) { router.push("/"); return; }
    Promise.all([
      api.get("/admin/data-quality").catch(() => ({ data: null })),
      api.get("/students/options").then((r) => ({
        regions: r.data.regions,
        roles: r.data.roles,
        sectors: r.data.sectors,
        skills: r.data.skills,
      })).catch(() => ({ regions: [], roles: [], sectors: [], skills: [] })),
    ]).then(([d, o]) => {
      setDq(d.data);
      setRegions(o.regions);
      setRoles(o.roles);
      setSectors(o.sectors);
      setSkills(o.skills);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [isAdmin, router]);

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading…</div>;
  if (!isAdmin) return null;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
          <Database className="w-6 h-6 text-accent-400" /> Data management
        </h1>
        <p className="text-sm text-navy-600 mt-1">Data quality, seeding, CSV import, and reference data.</p>
      </div>

      {/* Data quality card */}
      <div className="card mb-6 border-navy-200">
        <div className="card-header">
          <h2 className="card-title flex items-center gap-2"><BarChart3 className="w-4 h-4 text-navy-500" /> Data quality</h2>
          {dq?.is_demo_data && <span className="badge-demo">DEMO DATA</span>}
        </div>
        {dq && (
          <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">Jobs analyzed</p>
              <p className="text-2xl font-bold text-navy-900">{dq.jobs_analyzed}</p>
            </div>
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">Jobs with skill extraction</p>
              <p className="text-2xl font-bold text-navy-900">{dq.jobs_with_skill_extraction} ({dq.percentage_with_extracted_skills}%)</p>
            </div>
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">Unique skills</p>
              <p className="text-2xl font-bold text-navy-900">{dq.unique_skills}</p>
            </div>
            <div>
              <p className="text-xs text-navy-500 uppercase tracking-wider">Confidence level</p>
              <p className="text-2xl font-bold text-navy-900">{dq.confidence_level}</p>
            </div>
          </div>
          {dq.note && <p className="text-xs text-navy-500 mt-3">{dq.note}</p>}
          <p className="text-xs text-navy-500 mt-2">Last data refresh: {dq.last_data_refresh || "not set"}</p>
          </>
        )}
      </div>

      <div className="card-grid mb-6">
        <div className="card flex items-center gap-4">
          <div className="flex-1">
            <h3 className="font-semibold text-navy-900">Import jobs (CSV)</h3>
            <p className="text-sm text-navy-600 mt-1">CSV columns: job_title, company, city, state, sector, description, posted_date, source, source_url</p>
            <label className="btn-secondary text-sm mt-3 cursor-pointer inline-flex items-center gap-2">
              <Upload className="w-4 h-4" /> Choose CSV
              <input type="file" accept=".csv" className="hidden" id="data-csv" onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                setLoading(true);
                try {
                  const form = new FormData();
                  form.append("file", file);
                  const res = await api.post("/admin/import-jobs", form, { headers: { "Content-Type": "multipart/form-data" } });
                  alert(`Imported ${res.data.imported}, skipped ${res.data.skipped}`);
                  refreshAll();
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
            <p className="mt-1">Region, role, and sector are auto-resolved from names when possible.</p>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="flex-1">
            <h3 className="font-semibold text-navy-900">Reseed demo dataset</h3>
            <p className="text-sm text-navy-600 mt-1">Reseed regions, roles, sectors, skills, and demo jobs.</p>
            <button
              onClick={async () => {
                if (!confirm("Reseed demo data? This will re-create demo jobs and skills.")) return;
                setLoading(true);
                try {
                  await api.post("/admin/seed-demo");
                  alert("Demo data reseeded.");
                  refreshAll();
                } catch (err: any) {
                  alert(err?.response?.data?.detail || "Seed failed");
                } finally {
                  setLoading(false);
                }
              }}
              className="btn-secondary text-sm mt-3"
            >
              <Hash className="w-4 h-4" /> Reseed
            </button>
          </div>
          <div className="hidden sm:block text-xs text-navy-500">
            <p className="font-medium text-navy-700">Note</p>
            <p className="mt-1">Demo data is labelled clearly. Never present it as live market data.</p>
          </div>
        </div>
      </div>

      {/* Reference data */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="card">
          <div className="card-header"><h2 className="card-title flex items-center gap-2"><Hash className="w-4 h-4" /> Regions ({regions.length})</h2></div>
          <div className="space-y-2">
            {regions.map((r) => (
              <div key={r.id} className="flex items-center justify-between text-sm">
                <span className="text-navy-900">{r.name}</span>
                <span className={`text-xs ${r.confidence_default === "high" ? "text-emerald-600" : r.confidence_default === "medium" ? "text-amber-600" : "text-red-600"}`}>
                  {r.confidence_default} confidence
                </span>
              </div>
            ))}
            {regions.length === 0 && <p className="text-sm text-navy-500">No regions</p>}
          </div>
        </div>
        <div className="card">
          <div className="card-header"><h2 className="card-title flex items-center gap-2"><Hash className="w-4 h-4" /> Roles ({roles.length})</h2></div>
          <div className="space-y-2">
            {roles.map((r) => (
              <div key={r.id} className="text-sm">
                <span className="text-navy-900">{r.name}</span>
                <span className="text-xs text-navy-500 ml-1">· {r.category || "—"}</span>
              </div>
            ))}
            {roles.length === 0 && <p className="text-sm text-navy-500">No roles</p>}
          </div>
        </div>
        <div className="card">
          <div className="card-header"><h2 className="card-title flex items-center gap-2"><Hash className="w-4 h-4" /> Sectors ({sectors.length})</h2></div>
          <div className="space-y-2">
            {sectors.map((s) => (
              <div key={s.id} className="text-sm">
                <span className="text-navy-900">{s.name}</span>
              </div>
            ))}
            {sectors.length === 0 && <p className="text-sm text-navy-500">No sectors</p>}
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-xl bg-navy-100 border border-navy-200 p-4 text-xs text-navy-600">
        <p className="font-medium text-navy-800">Data quality principles</p>
        <ul className="mt-1 space-y-1 list-disc list-inside">
          <li>Show the number of jobs analyzed, unique skills, and last refresh.</li>
          <li>Show the % of jobs with skill extraction — never hide extraction gaps.</li>
          <li>Show confidence level and label demo data clearly.</li>
          <li>Small-city fallback shows a confidence indicator; low-confidence data is not presented as high-confidence.</li>
        </ul>
      </div>
    </div>
  );
}

async function refreshAll() {
  // callers re-render via state
}
