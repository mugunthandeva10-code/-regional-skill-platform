"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Job, Region, Role, Sector } from "@/lib/types";
import {
  Plus, Edit2, Trash2, ExternalLink, MapPin, Tag, Calendar,
  ChevronDown, Save, X,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function AdminJobsPage() {
  const router = useRouter();
  const { isAdmin } = useAuth();
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [options, setOptions] = useState<{ regions: Region[]; roles: Role[]; sectors: Sector[] } | null>(null);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Job | null>(null);
  const [filter, setFilter] = useState({ regionId: "", roleId: "", sectorId: "", q: "" });

  const [form, setForm] = useState({
    job_title: "",
    company: "",
    region_id: "",
    city: "",
    state: "",
    sector_id: "",
    role_id: "",
    description: "",
    required_skills: "",
    optional_skills: "",
    experience_level: "Intermediate",
    posted_date: "",
    source: "",
    source_url: "",
    is_demo: false,
  });

  useEffect(() => {
    if (!isAdmin) { router.push("/"); return; }
    Promise.all([
      api.get("/jobs").catch(() => ({ data: [] })),
      api.get("/students/options").then((r) => ({ regions: r.data.regions, roles: r.data.roles, sectors: r.data.sectors })).catch(() => ({ regions: [], roles: [], sectors: [] })),
    ]).then(([j, o]) => {
      setJobs(j.data);
      setOptions(o);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [isAdmin, router]);

  const refresh = () => {
    api.get("/jobs").then((res) => setJobs(res.data)).catch(() => {});
  };

  const resetForm = () => {
    setForm({
      job_title: "", company: "", region_id: "", city: "", state: "", sector_id: "", role_id: "",
      description: "", required_skills: "", optional_skills: "", experience_level: "Intermediate",
      posted_date: "", source: "", source_url: "", is_demo: false,
    });
    setEditing(null);
    setShowForm(false);
  };

  const save = async () => {
    if (!form.job_title.trim()) return;
    setSaving(true);
    try {
      const body = {
        job_title: form.job_title,
        company: form.company,
        region_id: form.region_id || undefined,
        city: form.city,
        state: form.state,
        sector_id: form.sector_id || undefined,
        role_id: form.role_id || undefined,
        description: form.description,
        required_skills: form.required_skills.split(",").map((s) => s.trim()).filter(Boolean),
        optional_skills: form.optional_skills.split(",").map((s) => s.trim()).filter(Boolean),
        experience_level: form.experience_level,
        posted_date: form.posted_date || undefined,
        source: form.source,
        source_url: form.source_url,
        is_demo: form.is_demo,
      };
      if (editing) {
        await api.put(`/jobs/${editing.id}`, body);
      } else {
        await api.post("/jobs", body);
      }
      refresh();
      resetForm();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (j: Job) => {
    setForm({
      job_title: j.job_title,
      company: j.company || "",
      region_id: j.region_id || "",
      city: j.city || "",
      state: j.state || "",
      sector_id: j.sector_id || "",
      role_id: j.role_id || "",
      description: j.description || "",
      required_skills: (j.required_skills || []).join(", "),
      optional_skills: (j.optional_skills || []).join(", "),
      experience_level: j.experience_level || "Intermediate",
      posted_date: j.posted_date || "",
      source: j.source || "",
      source_url: j.source_url || "",
      is_demo: j.is_demo,
    });
    setEditing(j);
    setShowForm(true);
  };

  const deleteJob = async (id: string) => {
    if (!confirm("Delete this job?")) return;
    try {
      await api.delete(`/jobs/${id}`);
      refresh();
    } catch {}
  };

  const filtered = jobs.filter((j) => {
    if (filter.regionId && j.region_id !== filter.regionId) return false;
    if (filter.roleId && j.role_id !== filter.roleId) return false;
    if (filter.sectorId && j.sector_id !== filter.sectorId) return false;
    if (filter.q && !j.job_title.toLowerCase().includes(filter.q.toLowerCase()) && !(j.company || "").toLowerCase().includes(filter.q.toLowerCase())) return false;
    return true;
  });

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading…</div>;
  if (!isAdmin) return null;

  return (
    <div>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
            <MapPin className="w-6 h-6 text-accent-400" /> Job management
          </h1>
          <p className="text-sm text-navy-600 mt-1">{jobs.length} jobs total</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { resetForm(); setShowForm(true); }} className="btn-primary text-sm">
            <Plus className="w-4 h-4" /> Add job
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={filter.q}
            onChange={(e) => setFilter((f) => ({ ...f, q: e.target.value }))}
            className="input-field w-48"
            placeholder="Search jobs…"
          />
          <select value={filter.regionId} onChange={(e) => setFilter((f) => ({ ...f, regionId: e.target.value }))} className="input-field w-40">
            <option value="">All regions</option>
            {options?.regions.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
          </select>
          <select value={filter.roleId} onChange={(e) => setFilter((f) => ({ ...f, roleId: e.target.value }))} className="input-field w-40">
            <option value="">All roles</option>
            {options?.roles.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
          </select>
          <select value={filter.sectorId} onChange={(e) => setFilter((f) => ({ ...f, sectorId: e.target.value }))} className="input-field w-32">
            <option value="">All sectors</option>
            {options?.sectors.map((s) => (<option key={s.id} value={s.id}>{s.name}</option>))}
          </select>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <div className="card mb-6 border-accent-400 bg-accent-50/30">
          <div className="card-header">
            <h2 className="card-title">{editing ? "Edit job" : "Add job"}</h2>
            <button onClick={resetForm} className="btn-ghost text-xs">Cancel</button>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-navy-700 mb-1">Job title *</label>
              <input value={form.job_title} onChange={(e) => setForm((f) => ({ ...f, job_title: e.target.value }))} className="input-field" placeholder="Backend Developer" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Company</label>
              <input value={form.company} onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))} className="input-field" placeholder="Company name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Region</label>
              <select value={form.region_id} onChange={(e) => setForm((f) => ({ ...f, region_id: e.target.value }))} className="input-field">
                <option value="">Select region</option>
                {options?.regions.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">City</label>
              <input value={form.city} onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))} className="input-field" placeholder="Chennai" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">State</label>
              <input value={form.state} onChange={(e) => setForm((f) => ({ ...f, state: e.target.value }))} className="input-field" placeholder="Tamil Nadu" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Role</label>
              <select value={form.role_id} onChange={(e) => setForm((f) => ({ ...f, role_id: e.target.value }))} className="input-field">
                <option value="">Select role</option>
                {options?.roles.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Sector</label>
              <select value={form.sector_id} onChange={(e) => setForm((f) => ({ ...f, sector_id: e.target.value }))} className="input-field">
                <option value="">Select sector</option>
                {options?.sectors.map((s) => (<option key={s.id} value={s.id}>{s.name}</option>))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-navy-700 mb-1">Description</label>
              <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} className="input-field min-h-[80px]" placeholder="Job description…" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Required skills (comma separated)</label>
              <input value={form.required_skills} onChange={(e) => setForm((f) => ({ ...f, required_skills: e.target.value }))} className="input-field" placeholder="Java, SQL, REST APIs, Docker" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Optional skills (comma separated)</label>
              <input value={form.optional_skills} onChange={(e) => setForm((f) => ({ ...f, optional_skills: e.target.value }))} className="input-field" placeholder="AWS, Kubernetes" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Experience level</label>
              <select value={form.experience_level} onChange={(e) => setForm((f) => ({ ...f, experience_level: e.target.value }))} className="input-field">
                <option>Entry</option>
                <option>Intermediate</option>
                <option>Mid</option>
                <option>Senior</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Posted date (YYYY-MM-DD)</label>
              <input type="date" value={form.posted_date} onChange={(e) => setForm((f) => ({ ...f, posted_date: e.target.value }))} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Source</label>
              <input value={form.source} onChange={(e) => setForm((f) => ({ ...f, source: e.target.value }))} className="input-field" placeholder="Demo seed" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Source URL</label>
              <input value={form.source_url} onChange={(e) => setForm((f) => ({ ...f, source_url: e.target.value }))} className="input-field" placeholder="https://…" />
            </div>
            <div className="sm:col-span-2 flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-navy-700">
                <input type="checkbox" checked={form.is_demo} onChange={(e) => setForm((f) => ({ ...f, is_demo: e.target.checked }))} className="rounded border-surface-line text-accent-400 focus:ring-accent-400" />
                Mark as demo data
              </label>
              <button onClick={save} disabled={saving || !form.job_title.trim()} className="btn-primary text-sm disabled:opacity-50">
                <Save className="w-4 h-4" /> {saving ? "Saving…" : editing ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* List */}
      <div className="rounded-xl border border-surface-line bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-line bg-navy-100 text-left text-xs text-navy-600 uppercase tracking-wider">
                <th className="px-4 py-3 font-medium">Job title</th>
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Region / City</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Skills (req)</th>
                <th className="px-4 py-3 font-medium">Demo</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((j) => (
                <tr key={j.id} className="border-b border-surface-line last:border-0 hover:bg-navy-50 transition">
                  <td className="px-4 py-3 font-medium text-navy-900">{j.job_title}</td>
                  <td className="px-4 py-3 text-navy-600">{j.company || "—"}</td>
                  <td className="px-4 py-3 text-navy-600">
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3 text-navy-400" /> {j.region?.name || j.city || "—"}</span>
                  </td>
                  <td className="px-4 py-3">{j.role?.name || "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(j.required_skills || []).slice(0, 4).map((s) => (
                        <span key={s} className="text-xs px-2 py-0.5 rounded bg-navy-100 text-navy-700">{s}</span>
                      ))}
                      {(j.required_skills || []).length > 4 && <span className="text-xs text-navy-400">+{(j.required_skills || []).length - 4}</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {j.is_demo && <span className="badge-demo">DEMO</span>}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => startEdit(j)} className="btn-ghost text-xs p-1.5"><Edit2 className="w-3.5 h-3.5" /></button>
                      <button onClick={() => deleteJob(j.id)} className="btn-ghost text-xs p-1.5 text-red-500 hover:text-red-700"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-navy-500 text-sm">No jobs match the filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
