"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import {
  Profile, Region, Role, Sector, Skill, StudentSkill, Project,
  ExtractedSkill, OptionsBucket,
} from "@/lib/types";
import SkillPill from "@/components/ui/SkillPill";
import {
  User, GraduationCap, MapPin, Briefcase, Upload, FileText,
  Save, Check, Trash2, Plus, X, ArrowRight, ExternalLink,
} from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [options, setOptions] = useState<OptionsBucket | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [skills, setSkills] = useState<StudentSkill[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [extracted, setExtracted] = useState<ExtractedSkill[]>([]);
  const [resumeId, setResumeId] = useState<string | null>(null);

  const [personal, setPersonal] = useState({
    college: user?.college || "",
    department: user?.department || "",
    degree: user?.degree || "",
    graduationYear: user?.graduation_year || "",
    location: user?.location || "",
  });

  const [career, setCareer] = useState({
    targetRoleId: profile?.target_role_id || "",
    targetSectorId: profile?.target_sector_id || "",
    preferredRegionId: profile?.preferred_region_id || "",
  });

  const [summary, setSummary] = useState(profile?.summary || "");
  const [skillsDraft, setSkillsDraft] = useState<{ skillId: string; level: string }[]>([]);

  // Form state for new project
  const [newProject, setNewProject] = useState({ name: "", description: "", technologies: "", githubUrl: "", demoUrl: "", screenshotUrl: "", status: "in_progress" });
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([
      api.get("/students/options"),
      api.get("/students/profile").catch(() => ({ data: null })),
      api.get("/students/skills").catch(() => ({ data: [] })),
      api.get("/students/projects").catch(() => ({ data: [] })),
    ]).then(([opt, prof, sk, pj]) => {
      setOptions(opt.data);
      setProfile(prof.data);
      setSkills(sk.data);
      setProjects(pj.data);
      setSaving(false);
      setLoading(false);

      if (prof.data) {
        setCareer({
          targetRoleId: prof.data.target_role_id || "",
          targetSectorId: prof.data.target_sector_id || "",
          preferredRegionId: prof.data.preferred_region_id || "",
        });
        setSummary(prof.data.summary || "");
      }
    }).catch(() => setLoading(false));
  }, []);

  const refreshSkills = () => {
    api.get("/students/skills").then((res) => setSkills(res.data)).catch(() => {});
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSaving(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await api.post("/students/resume", form, { headers: { "Content-Type": "multipart/form-data" } });
      setExtracted(res.data.extracted_skills);
      setResumeId(res.data.id);
      // Auto-suggest skills from extracted (user must confirm)
      const existingIds = new Set(skills.map((s) => s.skill_id));
      const toAdd: { skillId: string; level: string }[] = [];
      for (const ex of res.data.extracted_skills) {
        const matched = options?.skills.find((s) => s.name === ex.normalized);
        if (matched && !existingIds.has(matched.id)) {
          toAdd.push({ skillId: matched.id, level: "beginner" });
        }
      }
      if (toAdd.length) {
        setSkillsDraft((prev) => [...prev, ...toAdd]);
      }
      refreshSkills();
      setSaving(false);
    } catch (err: any) {
      setSaving(false);
      alert(err?.response?.data?.detail || "Resume processing failed");
    }
    e.target.value = "";
  };

  const saveProfile = async () => {
    setSaving(true);
    try {
      const body: any = {
        summary,
      };
      if (career.targetRoleId) body.target_role_id = career.targetRoleId;
      if (career.targetSectorId) body.target_sector_id = career.targetSectorId;
      if (career.preferredRegionId) body.preferred_region_id = career.preferredRegionId;
      await api.put("/students/profile", body);

      // Save personal info to user
      await api.put("/auth/me", {
        college: personal.college,
        department: personal.department,
        degree: personal.degree,
        graduation_year: personal.graduationYear ? parseInt(String(personal.graduationYear), 10) : undefined,
        location: personal.location,
      });

      refreshSkills();
      router.push("/dashboard");
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Could not save profile");
    } finally {
      setSaving(false);
    }
  };

  const saveSkills = async () => {
    setSaving(true);
    try {
      const body = skillsDraft.map((d) => ({
        skill_id: d.skillId,
        level: d.level as any,
        source: "manual",
        confidence: 1,
        is_confirmed: true,
      }));
      await api.put("/students/skills", body);
      refreshSkills();
      setSkillsDraft([]);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Could not save skills");
    } finally {
      setSaving(false);
    }
  };

  const removeSkill = (skillId: string) => {
    setSkillsDraft((prev) => prev.filter((s) => s.skillId !== skillId));
  };

  const createProject = async () => {
    if (!newProject.name.trim()) return;
    setSaving(true);
    try {
      const body = {
        name: newProject.name,
        description: newProject.description,
        technologies: newProject.technologies.split(",").map((t) => t.trim()).filter(Boolean),
        github_url: newProject.githubUrl,
        demo_url: newProject.demoUrl,
        screenshot_url: newProject.screenshotUrl,
        status: newProject.status,
      };
      const res = await api.post("/students/projects", body);
      setProjects((prev) => [res.data, ...prev]);
      setNewProject({ name: "", description: "", technologies: "", githubUrl: "", demoUrl: "", screenshotUrl: "", status: "in_progress" });
      setSaving(false);
    } catch (err: any) {
      setSaving(false);
      alert(err?.response?.data?.detail || "Could not create project");
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading profile…</div>;

  const selectedRole = options?.roles.find((r) => r.id === career.targetRoleId);
  const selectedSector = options?.sectors.find((s) => s.id === career.targetSectorId);
  const selectedRegion = options?.regions.find((r) => r.id === career.preferredRegionId);

  const unusedSkills = options?.skills.filter((s) => !skillsDraft.some((d) => d.skillId === s.id) && !skills.some((ss) => ss.skill_id === s.id) && s.is_active);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900">Your profile</h1>
        <p className="text-sm text-navy-600 mt-1">{user?.full_name} · {user?.email}</p>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h2 className="card-title flex items-center gap-2"><User className="w-4 h-4 text-navy-500" /> Personal info</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">College</label>
            <input value={personal.college} onChange={(e) => setPersonal((p) => ({ ...p, college: e.target.value }))} className="input-field" placeholder="College name" />
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Department</label>
            <input value={personal.department} onChange={(e) => setPersonal((p) => ({ ...p, department: e.target.value }))} className="input-field" placeholder="e.g. CSE" />
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Degree</label>
            <input value={personal.degree} onChange={(e) => setPersonal((p) => ({ ...p, degree: e.target.value }))} className="input-field" placeholder="e.g. B.Tech" />
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Graduation year</label>
            <input type="number" value={personal.graduationYear} onChange={(e) => setPersonal((p) => ({ ...p, graduationYear: e.target.value }))} className="input-field" placeholder="2026" />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-navy-700 mb-1">Current city</label>
            <input value={personal.location} onChange={(e) => setPersonal((p) => ({ ...p, location: e.target.value }))} className="input-field" placeholder="City" />
          </div>
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h2 className="card-title flex items-center gap-2"><Briefcase className="w-4 h-4 text-navy-500" /> Career target</h2>
          {selectedRole && <span className="badge-demo">{selectedRole.name}</span>}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Target job role</label>
            <select value={career.targetRoleId} onChange={(e) => setCareer((c) => ({ ...c, targetRoleId: e.target.value }))} className="input-field">
              <option value="">Select a target role</option>
              {options?.roles.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
            </select>
            {selectedRole && <p className="text-xs text-navy-500 mt-1">{selectedRole.description}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Target sector</label>
            <select value={career.targetSectorId} onChange={(e) => setCareer((c) => ({ ...c, targetSectorId: e.target.value }))} className="input-field">
              <option value="">Select a sector (optional)</option>
              {options?.sectors.map((s) => (<option key={s.id} value={s.id}>{s.name}</option>))}
            </select>
            {selectedSector && <p className="text-xs text-navy-500 mt-1">{selectedSector.description}</p>}
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-navy-700 mb-1">Preferred region</label>
            <select value={career.preferredRegionId} onChange={(e) => setCareer((c) => ({ ...c, preferredRegionId: e.target.value }))} className="input-field">
              <option value="">Select a region</option>
              {options?.regions.map((r) => (<option key={r.id} value={r.id}>{r.name} — {r.city} · {r.state}</option>))}
            </select>
          </div>
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h2 className="card-title flex items-center gap-2"><FileText className="w-4 h-4 text-navy-500" /> Skills</h2>
          <span className="text-sm text-navy-500">{skills.length} confirmed · {skillsDraft.length} pending</span>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-navy-700 mb-2">Your confirmed skills</label>
          {skills.length === 0 ? (
            <p className="text-sm text-navy-500">No skills yet. Add below or upload a resume to detect them.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {skills.map((ss) => (
                <SkillPill key={ss.id} skill={ss.skill!} status={ss.level === "none" ? "missing" : ss.level === "beginner" ? "partial" : "matched"} level={ss.level} />
              ))}
            </div>
          )}
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-navy-700 mb-2">Add skills</label>
          <div className="flex flex-wrap gap-2">
            {unusedSkills?.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`skill-pill ${skillsDraft.some((d) => d.skillId === s.id) ? "ring-2 ring-accent-400 border-accent-400" : "bg-navy-100 text-navy-800 border-navy-200"}`}
                onClick={() => {
                  setSkillsDraft((prev) => {
                    if (prev.some((d) => d.skillId === s.id)) return prev;
                    return [...prev, { skillId: s.id, level: "beginner" }];
                  });
                }}
              >
                <Plus className="w-3.5 h-3.5" /> {s.name}
              </button>
            ))}
            {unusedSkills && unusedSkills.length === 0 && (
              <p className="text-sm text-navy-500">All skills added or none available.</p>
            )}
          </div>
        </div>

        {skillsDraft.length > 0 && (
          <div className="rounded-xl border border-surface-line bg-white p-4 mb-4">
            <p className="text-sm font-medium text-navy-900 mb-2">Pending skills — confirm or adjust</p>
            <div className="space-y-2">
              {skillsDraft.map((d) => {
                const sk = options?.skills.find((s) => s.id === d.skillId);
                return (
                  <div key={d.skillId} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-navy-100">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-navy-900 text-sm">{sk?.name}</span>
                      <select
                        value={d.level}
                        onChange={(e) => setSkillsDraft((prev) => prev.map((x) => (x.skillId === d.skillId ? { ...x, level: e.target.value } : x)))}
                        className="text-xs rounded border border-surface-line bg-white px-2 py-1"
                      >
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                      </select>
                    </div>
                    <button type="button" onClick={() => removeSkill(d.skillId)} className="text-red-500 hover:text-red-700">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div>
          <button onClick={saveSkills} disabled={saving || skillsDraft.length === 0} className="btn-secondary text-sm disabled:opacity-50">
            {saving ? "Saving…" : "Save skills"}
          </button>
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h2 className="card-title flex items-center gap-2"><Upload className="w-4 h-4 text-navy-500" /> Resume</h2>
        </div>
        <div className="flex items-center gap-4">
          <label className="btn-secondary cursor-pointer flex items-center gap-2 text-sm">
            <Upload className="w-4 h-4" /> Upload PDF
            <input type="file" accept=".pdf" ref={fileRef} onChange={handleFileChange} className="hidden" disabled={saving} />
          </label>
          {resumeId && (
            <span className="text-sm text-navy-600 flex items-center gap-1">
              <Check className="w-4 h-4 text-emerald-500" /> Uploaded
            </span>
          )}
          {saving && <span className="text-sm text-navy-600">Processing…</span>}
        </div>

        {extracted.length > 0 && (
          <div className="mt-4 rounded-xl border border-accent-400 bg-accent-50/40 p-4">
            <p className="text-sm font-medium text-accent-700 mb-2">
              Skills detected in resume — confirm or edit below
            </p>
            <div className="space-y-2">
              {extracted.map((ex, i) => {
                const sk = options?.skills.find((s) => s.name === ex.normalized || s.name === ex.name);
                return (
                  <div key={i} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-white border border-surface-line">
                    <div>
                      <p className="text-sm text-navy-900">{ex.name}</p>
                      <p className="text-xs text-navy-500">Normalized: <span className="font-mono">{ex.normalized || ex.name}</span> · confidence {ex.confidence.toFixed(2)}</p>
                    </div>
                    {sk && !skillsDraft.some((d) => d.skillId === sk.id) ? (
                      <button
                        type="button"
                        className="btn-ghost text-xs"
                        onClick={() => setSkillsDraft((prev) => [...prev, { skillId: sk.id, level: "beginner" }])}
                      >
                        Add to profile
                      </button>
                    ) : sk && skillsDraft.some((d) => d.skillId === sk.id) ? (
                      <span className="text-xs text-emerald-600">Added</span>
                    ) : (
                      <span className="text-xs text-navy-500">Not in taxonomy yet</span>
                    )}
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-navy-500 mt-2">AI NEVER silently adds skills. You confirm each one.</p>
          </div>
        )}
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h2 className="card-title flex items-center gap-2"><Briefcase className="w-4 h-4 text-navy-500" /> Projects / proof</h2>
          <span className="text-sm text-navy-500">{projects.length} projects</span>
        </div>

        <div className="flex items-center gap-2 mb-4">
          <input
            value={newProject.name}
            onChange={(e) => setNewProject((p) => ({ ...p, name: e.target.value }))}
            className="input-field flex-1"
            placeholder="Project name"
          />
          <button onClick={createProject} disabled={saving || !newProject.name.trim()} className="btn-primary text-sm whitespace-nowrap">
            <Plus className="w-4 h-4" /> Add
          </button>
        </div>

        <div className="space-y-3">
          {projects.map((pj) => (
            <div key={pj.id} className="rounded-xl border border-surface-line bg-white p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-navy-900">{pj.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${pj.status === "completed" ? "bg-emerald-50 text-emerald-700" : pj.status === "in_progress" ? "bg-amber-50 text-amber-700" : "bg-navy-100 text-navy-600"}`}>{pj.status}</span>
                  </div>
                  {pj.description && <p className="text-sm text-navy-600 mt-1">{pj.description}</p>}
                  {pj.technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {pj.technologies.map((t) => (
                        <span key={t} className="skill-pill skill-pill-neutral text-xs" style={{ backgroundColor: "#f1f5f9", color: "#334155", borderColor: "#cbd5e1" }}>{t}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-col gap-1">
                  {pj.github_url && (
                    <a href={pj.github_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs flex items-center gap-1 text-navy-600">
                      <ExternalLink className="w-3 h-3" /> GitHub
                    </a>
                  )}
                  {pj.demo_url && (
                    <a href={pj.demo_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs flex items-center gap-1 text-navy-600">
                      <ExternalLink className="w-3 h-3" /> Demo
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
          {projects.length === 0 && (
            <p className="text-sm text-navy-500 text-center py-4">No projects yet. Add project proof as you complete roadmap tasks.</p>
          )}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-end">
        <button onClick={saveProfile} disabled={saving} className="btn-primary disabled:opacity-60">
          {saving ? "Saving…" : <><Save className="w-4 h-4" /> Save profile</>}
        </button>
        <button onClick={() => router.push("/dashboard")} className="btn-secondary">
          Back to dashboard
        </button>
      </div>
    </div>
  );
}
