"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Project } from "@/lib/types";
import {
  Plus, ExternalLink, GitBranch, Image, Trash2, Edit2, Save, X,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function ProjectsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);

  const [form, setForm] = useState({
    name: "",
    description: "",
    technologies: "",
    githubUrl: "",
    demoUrl: "",
    screenshotUrl: "",
    status: "in_progress",
  });

  useEffect(() => {
    api.get("/students/projects").then((res) => {
      setProjects(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const resetForm = () => {
    setForm({ name: "", description: "", technologies: "", githubUrl: "", demoUrl: "", screenshotUrl: "", status: "in_progress" });
    setEditing(null);
    setShowForm(false);
  };

  const save = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const body = {
        name: form.name,
        description: form.description,
        technologies: form.technologies.split(",").map((t) => t.trim()).filter(Boolean),
        github_url: form.githubUrl,
        demo_url: form.demoUrl,
        screenshot_url: form.screenshotUrl,
        status: form.status,
      };
      if (editing) {
        await api.put(`/students/projects/${editing.id}`, body);
      } else {
        await api.post("/students/projects", body);
      }
      refresh();
      resetForm();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Could not save project");
    } finally {
      setSaving(false);
    }
  };

  const refresh = () => {
    api.get("/students/projects").then((res) => setProjects(res.data)).catch(() => {});
  };

  const startEdit = (p: Project) => {
    setForm({
      name: p.name,
      description: p.description || "",
      technologies: (p.technologies || []).join(", "),
      githubUrl: p.github_url || "",
      demoUrl: p.demo_url || "",
      screenshotUrl: p.screenshot_url || "",
      status: p.status,
    });
    setEditing(p);
    setShowForm(true);
  };

  const deleteProject = async (id: string) => {
    if (!confirm("Delete this project?")) return;
    try {
      await api.delete(`/students/projects/${id}`);
      refresh();
    } catch {}
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading projects…</div>;

  return (
    <div>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-accent-400" /> Projects & proof
          </h1>
          <p className="text-sm text-navy-600 mt-1">
            Build and attach proof for your skills — GitHub, demo links, screenshots.
          </p>
        </div>
        <button onClick={() => { resetForm(); setShowForm(true); }} className="btn-primary text-sm">
          <Plus className="w-4 h-4" /> New project
        </button>
      </div>

      {showForm && (
        <div className="card mb-6 border-accent-400 bg-accent-50/30">
          <div className="card-header">
            <h2 className="card-title">{editing ? "Edit project" : "New project"}</h2>
            <button onClick={resetForm} className="btn-ghost text-xs">Cancel</button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Project name *</label>
              <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className="input-field" placeholder="e.g. Containerized Student Attendance API" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Description</label>
              <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} className="input-field min-h-[80px]" placeholder="What does this project demonstrate?" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Technologies (comma separated)</label>
              <input value={form.technologies} onChange={(e) => setForm((f) => ({ ...f, technologies: e.target.value }))} className="input-field" placeholder="Java, Spring Boot, Docker, PostgreSQL" />
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-navy-700 mb-1">GitHub URL</label>
                <input value={form.githubUrl} onChange={(e) => setForm((f) => ({ ...f, githubUrl: e.target.value }))} className="input-field" placeholder="https://github.com/..." />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy-700 mb-1">Demo URL</label>
                <input value={form.demoUrl} onChange={(e) => setForm((f) => ({ ...f, demoUrl: e.target.value }))} className="input-field" placeholder="https://..." />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Screenshot URL</label>
              <input value={form.screenshotUrl} onChange={(e) => setForm((f) => ({ ...f, screenshotUrl: e.target.value }))} className="input-field" placeholder="https://... screenshot of the project" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Status</label>
              <select value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))} className="input-field">
                <option value="planned">Planned</option>
                <option value="in_progress">In progress</option>
                <option value="completed">Completed</option>
              </select>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={save} disabled={saving || !form.name.trim()} className="btn-primary text-sm disabled:opacity-50">
                <Save className="w-4 h-4" /> {saving ? "Saving…" : editing ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((p) => (
          <div key={p.id} className="rounded-xl border border-surface-line bg-white p-4 hover:border-navy-200 transition">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-navy-900 truncate">{p.name}</h3>
                  <span className={cn("text-xs px-2 py-0.5 rounded-full shrink-0", p.status === "completed" && "bg-emerald-50 text-emerald-700", p.status === "in_progress" && "bg-amber-50 text-amber-700", p.status === "planned" && "bg-navy-100 text-navy-600")}>
                    {p.status}
                  </span>
                </div>
                {p.description && <p className="text-sm text-navy-600 mt-1 line-clamp-2">{p.description}</p>}
                {p.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {p.technologies.map((t) => (
                      <span key={t} className="text-xs px-2 py-0.5 rounded bg-navy-100 text-navy-700">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 pt-2 border-t border-surface-line">
              <button onClick={() => startEdit(p)} className="btn-ghost text-xs flex items-center gap-1"><Edit2 className="w-3 h-3" /> Edit</button>
              {p.github_url && (
                <a href={p.github_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs flex items-center gap-1 text-navy-600">
                  <GitBranch className="w-3 h-3" /> GitHub
                </a>
              )}
              {p.demo_url && (
                <a href={p.demo_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs flex items-center gap-1 text-navy-600">
                  <ExternalLink className="w-3 h-3" /> Demo
                </a>
              )}
              {p.screenshot_url && (
                <a href={p.screenshot_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs flex items-center gap-1 text-navy-600">
                  <Image className="w-3 h-3" /> Preview
                </a>
              )}
              <button onClick={() => deleteProject(p.id)} className="btn-ghost text-xs text-red-500 hover:text-red-700 ml-auto flex items-center gap-1">
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
        {projects.length === 0 && (
          <div className="col-span-full rounded-xl border border-surface-line bg-white p-8 text-center">
            <GitBranch className="w-8 h-8 text-navy-300 mx-auto mb-3" />
            <p className="text-navy-700 font-medium">No projects yet</p>
            <p className="text-sm text-navy-500 mt-1">Create a project to prove your skills to employers.</p>
          </div>
        )}
      </div>
    </div>
  );
}
