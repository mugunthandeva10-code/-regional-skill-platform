"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { StudentSkill, Skill, ExtractedSkill } from "@/lib/types";
import {
  Plus, Trash2, Upload, FileText, Check, X, ArrowRight, BookOpen,
  AlertTriangle, Search,
} from "lucide-react";
import { cn } from "@/lib/utils";

const LEVELS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
] as const;

const levelStyle: Record<string, string> = {
  advanced: "bg-navy-600 text-white border-navy-600",
  intermediate: "bg-blue-50 text-navy-700 border-blue-200",
  beginner: "bg-amber-50 text-amber-700 border-amber-200",
  none: "bg-surface text-navy-500 border-surface-line",
};

export default function SkillsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<"manual" | "resume">("manual");

  const [mySkills, setMySkills] = useState<StudentSkill[]>([]);
  const [allSkills, setAllSkills] = useState<Skill[]>([]);
  const [query, setQuery] = useState("");
  const [detected, setDetected] = useState<ExtractedSkill[]>([]);
  const [resumeMsg, setResumeMsg] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    const [sk, all] = await Promise.all([
      api.get("/students/skills").then((r) => r.data),
      api.get("/students/options").then((r) => r.data.skills),
    ]);
    setMySkills(sk);
    setAllSkills(all);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const mine = new Map(mySkills.map((s) => [s.skill_id, s]));
  const available = allSkills.filter(
    (s) => !mine.has(s.id) && s.name.toLowerCase().includes(query.toLowerCase())
  );

  const addSkill = async (skillId: string, level = "beginner") => {
    try {
      await api.put("/students/skills", [
        { skill_id: skillId, level, source: "manual", confidence: 1, is_confirmed: true },
      ]);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not add skill");
    }
  };

  const setLevel = async (skillId: string, level: string) => {
    const current = mine.get(skillId);
    if (!current) return;
    try {
      await api.put("/students/skills", [
        { skill_id: skillId, level, source: current.source, confidence: current.confidence, is_confirmed: true },
      ]);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not update skill");
    }
  };

  const removeSkill = async (skillId: string) => {
    try {
      await api.delete(`/students/skills/${skillId}`);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not remove skill");
    }
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSaving(true);
    setError("");
    setResumeMsg("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await api.post("/students/resume", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setDetected(res.data.extracted_skills);
      setResumeMsg(res.data.message);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Resume processing failed. You can add skills manually.");
    } finally {
      setSaving(false);
      if (e.target) e.target.value = "";
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[60vh]">Loading skills…</div>;
  }

  const counts = {
    total: mySkills.length,
    advanced: mySkills.filter((s) => s.level === "advanced").length,
    intermediate: mySkills.filter((s) => s.level === "intermediate").length,
    beginner: mySkills.filter((s) => s.level === "beginner").length,
  };

  return (
    <div>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-accent-400" /> Your skills
          </h1>
          <p className="text-sm text-navy-600 mt-1">
            Add the skills you actually have. These are compared against regional market demand to find your gaps.
          </p>
        </div>
        <Link href="/gap" className="btn-primary text-sm self-start">
          Compare with market <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 mb-4">{error}</div>
      )}

      <div className="card-grid mb-6">
        <div className="card text-center">
          <p className="text-3xl font-bold text-navy-900">{counts.total}</p>
          <p className="text-xs text-navy-500 mt-1 uppercase tracking-wider">Total skills</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-navy-900">{counts.advanced}</p>
          <p className="text-xs text-navy-500 mt-1 uppercase tracking-wider">Advanced</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-navy-900">{counts.intermediate}</p>
          <p className="text-xs text-navy-500 mt-1 uppercase tracking-wider">Intermediate</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-navy-900">{counts.beginner}</p>
          <p className="text-xs text-navy-500 mt-1 uppercase tracking-wider">Beginner</p>
        </div>
      </div>

      <div className="card mb-6">
        <div className="flex gap-2 mb-5">
          {(["manual", "resume"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                "px-4 py-2 rounded-xl text-sm font-medium transition",
                tab === t ? "bg-navy-600 text-white" : "bg-navy-100 text-navy-700 hover:bg-navy-200",
              )}
            >
              {t === "manual" ? "Add manually" : "Import from resume"}
            </button>
          ))}
        </div>

        {tab === "manual" ? (
          <>
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="input-field pl-9"
                placeholder="Search skills (Java, Docker, AWS, React…)"
              />
            </div>

            <p className="text-sm font-medium text-navy-700 mb-2">
              Add a skill — then set your level
            </p>
            <div className="flex flex-wrap gap-2">
              {available.slice(0, 40).map((s) => (
                <button
                  key={s.id}
                  onClick={() => addSkill(s.id)}
                  className="skill-pill skill-pill-neutral hover:ring-2 hover:ring-accent-400"
                >
                  <Plus className="w-3.5 h-3.5" /> {s.name}
                  {s.category && <span className="text-[10px] text-navy-400">· {s.category}</span>}
                </button>
              ))}
              {available.length === 0 && (
                <p className="text-sm text-navy-500">
                  {query ? "No skills match your search." : "All skills are already on your profile."}
                </p>
              )}
            </div>
            {available.length > 40 && (
              <p className="text-xs text-navy-500 mt-3">Showing 40 of {available.length}. Refine with search.</p>
            )}
          </>
        ) : (
          <>
            <label className="btn-secondary cursor-pointer inline-flex items-center gap-2 text-sm">
              <Upload className="w-4 h-4" /> Upload resume (PDF, max 5MB)
              <input type="file" accept=".pdf" ref={fileRef} onChange={onUpload} className="hidden" disabled={saving} />
            </label>
            {saving && <p className="text-sm text-navy-600 mt-3">Extracting skills from your resume…</p>}
            {resumeMsg && <p className="text-sm text-emerald-600 mt-3">{resumeMsg}</p>}

            {detected.length > 0 && (
              <div className="mt-5 rounded-xl border border-accent-400 bg-accent-50/40 p-4">
                <p className="text-sm font-medium text-accent-700 mb-1">
                  Skills detected in your resume
                </p>
                <p className="text-xs text-accent-600 mb-3">
                  Nothing is added automatically. Review and confirm each one.
                </p>
                <div className="space-y-2">
                  {detected.map((ex, i) => {
                    const match = allSkills.find((s) => s.name === ex.normalized || s.name === ex.name);
                    const already = match ? mine.has(match.id) : false;
                    return (
                      <div key={i} className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-white border border-surface-line">
                        <div className="min-w-0">
                          <p className="text-sm text-navy-900">{ex.name}</p>
                          <p className="text-xs text-navy-500">
                            Normalized to <span className="font-mono">{ex.normalized || ex.name}</span>
                            {" · "}confidence {ex.confidence.toFixed(2)}
                          </p>
                        </div>
                        {match ? (
                          already ? (
                            <span className="text-xs text-emerald-600 flex items-center gap-1 shrink-0">
                              <Check className="w-3.5 h-3.5" /> On your profile
                            </span>
                          ) : (
                            <button
                              onClick={() => addSkill(match.id)}
                              className="btn-ghost text-xs shrink-0"
                            >
                              <Plus className="w-3.5 h-3.5" /> Add
                            </button>
                          )
                        ) : (
                          <span className="text-xs text-navy-400 shrink-0">Not in taxonomy yet</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title flex items-center gap-2">
            <FileText className="w-4 h-4 text-navy-500" /> Confirmed skills ({mySkills.length})
          </h2>
        </div>

        {mySkills.length === 0 ? (
          <div className="py-10 text-center">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
            <p className="text-navy-700 font-medium">No skills added yet</p>
            <p className="text-sm text-navy-500 mt-1">
              Add a few skills above so we can compare them against the market.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {mySkills.map((ss) => (
              <div
                key={ss.id}
                className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-surface-line bg-white"
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium text-navy-900 text-sm">
                    {ss.skill?.name || "Unknown skill"}
                  </span>
                  {ss.skill?.category && (
                    <span className="text-xs text-navy-400">· {ss.skill.category}</span>
                  )}
                  <span
                    className={cn(
                      "text-[10px] font-medium px-1.5 py-0.5 rounded border capitalize",
                      ss.source === "resume" ? "bg-accent-50 text-accent-700 border-accent-200" : "bg-navy-100 text-navy-600 border-navy-200",
                    )}
                  >
                    {ss.source}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    {LEVELS.map((lv) => (
                      <button
                        key={lv.value}
                        onClick={() => setLevel(ss.skill_id, lv.value)}
                        className={cn(
                          "text-xs px-2.5 py-1 rounded-lg border font-medium transition",
                          ss.level === lv.value
                            ? levelStyle[lv.value]
                            : "bg-white text-navy-500 border-surface-line hover:bg-navy-100",
                        )}
                      >
                        {lv.label}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => removeSkill(ss.skill_id)}
                    className="btn-ghost text-xs text-red-500 hover:text-red-700 hover:bg-red-50"
                    title="Remove skill"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 flex items-center justify-between border-t border-surface-line pt-4">
          <p className="text-xs text-navy-500">
            Skills marked <span className="text-navy-700">beginner</span> or <span className="text-navy-700">intermediate</span> may still count as a partial gap.
          </p>
          <Link href="/dashboard" className="btn-ghost text-sm">Done</Link>
        </div>
      </div>
    </div>
  );
}
