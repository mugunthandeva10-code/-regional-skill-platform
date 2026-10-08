"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Skill } from "@/lib/types";
import {
  Plus, Edit2, Trash2, Tag, Save, X, BookOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function AdminSkillsPage() {
  const router = useRouter();
  const { isAdmin } = useAuth();
  const [loading, setLoading] = useState(true);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Skill | null>(null);

  const [form, setForm] = useState({
    name: "",
    category: "",
    description: "",
    aliases: "",
    related_skill_ids: "",
  });

  useEffect(() => {
    if (!isAdmin) { router.push("/"); return; }
    api.get("/skills").then((res) => {
      setSkills(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [isAdmin, router]);

  const refresh = () => api.get("/skills").then((res) => setSkills(res.data)).catch(() => {});

  const resetForm = () => {
    setForm({ name: "", category: "", description: "", aliases: "", related_skill_ids: "" });
    setEditing(null);
    setShowForm(false);
  };

  const save = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const body = {
        name: form.name,
        category: form.category || undefined,
        description: form.description || undefined,
        aliases: form.aliases.split(",").map((a) => a.trim()).filter(Boolean),
        related_skill_ids: form.related_skill_ids.split(",").map((id) => id.trim()).filter(Boolean),
      };
      if (editing) {
        await api.put(`/skills/${editing.id}`, body);
      } else {
        await api.post("/skills", body);
      }
      refresh();
      resetForm();
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (s: Skill) => {
    setForm({
      name: s.name,
      category: s.category || "",
      description: s.description || "",
      aliases: (s.aliases || []).join(", "),
      related_skill_ids: (s.related_skill_ids || []).join(", "),
    });
    setEditing(s);
    setShowForm(true);
  };

  const deleteSkill = async (id: string) => {
    if (!confirm("Deactivate this skill?")) return;
    try {
      await api.delete(`/skills/${id}`);
      refresh();
    } catch {}
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading…</div>;
  if (!isAdmin) return null;

  return (
    <div>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
            <Tag className="w-6 h-6 text-accent-400" /> Skill taxonomy
          </h1>
          <p className="text-sm text-navy-600 mt-1">{skills.length} skills · aliases normalize different names to one skill</p>
        </div>
        <button onClick={() => { resetForm(); setShowForm(true); }} className="btn-primary text-sm">
          <Plus className="w-4 h-4" /> Add skill
        </button>
      </div>

      {showForm && (
        <div className="card mb-6 border-accent-400 bg-accent-50/30">
          <div className="card-header">
            <h2 className="card-title">{editing ? "Edit skill" : "Add skill"}</h2>
            <button onClick={resetForm} className="btn-ghost text-xs">Cancel</button>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Skill name *</label>
              <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className="input-field" placeholder="e.g. AWS" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Category</label>
              <input value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} className="input-field" placeholder="e.g. Cloud" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-navy-700 mb-1">Description</label>
              <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} className="input-field min-h-[80px]" placeholder="What this skill is about…" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Aliases (comma separated)</label>
              <input value={form.aliases} onChange={(e) => setForm((f) => ({ ...f, aliases: e.target.value }))} className="input-field" placeholder="Amazon Web Services, AWS Cloud, AWS" />
              <p className="text-xs text-navy-500 mt-1">Different names for the same skill are normalized here.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Related skill IDs (comma separated)</label>
              <input value={form.related_skill_ids} onChange={(e) => setForm((f) => ({ ...f, related_skill_ids: e.target.value }))} className="input-field" placeholder="UUIDs of related skills" />
            </div>
            <div className="sm:col-span-2 flex items-center gap-3">
              <button onClick={save} disabled={saving || !form.name.trim()} className="btn-primary text-sm disabled:opacity-50">
                <Save className="w-4 h-4" /> {saving ? "Saving…" : editing ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-surface-line bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-line bg-navy-100 text-left text-xs text-navy-600 uppercase tracking-wider">
                <th className="px-4 py-3 font-medium">Skill</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Aliases</th>
                <th className="px-4 py-3 font-medium">Related</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {skills.map((s) => (
                <tr key={s.id} className="border-b border-surface-line last:border-0 hover:bg-navy-50 transition">
                  <td className="px-4 py-3 font-medium text-navy-900">{s.name}</td>
                  <td className="px-4 py-3 text-navy-600">{s.category || "—"}</td>
                  <td className="px-4 py-3 text-navy-600 max-w-[200px] truncate" title={(s.aliases || []).join(", ")}>
                    {(s.aliases || []).length > 0 ? (s.aliases || []).join(", ") : "—"}
                  </td>
                  <td className="px-4 py-3 text-navy-600">{(s.related_skill_ids || []).length || 0}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => startEdit(s)} className="btn-ghost text-xs p-1.5"><Edit2 className="w-3.5 h-3.5" /></button>
                      <button onClick={() => deleteSkill(s.id)} className="btn-ghost text-xs p-1.5 text-red-500 hover:text-red-700"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
              {skills.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-navy-500 text-sm">No skills yet. Add the first skill.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6 rounded-xl bg-navy-100 border border-navy-200 p-4 text-xs text-navy-600">
        <p className="font-medium text-navy-800">Normalization example</p>
        <p className="mt-1">“Amazon Web Services”, “AWS”, and “AWS Cloud” should all be aliased to the canonical skill <strong>AWS</strong>. This ensures demand is counted correctly regardless of how a job posting phrases it.</p>
      </div>
    </div>
  );
}
