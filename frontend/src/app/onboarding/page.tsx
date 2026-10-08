"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Profile, Region, Role, Sector, Skill } from "@/lib/types";
import { Save, Check, ChevronDown, Plus } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [summary, setSummary] = useState("");
  const [options, setOptions] = useState<{ regions: Region[]; roles: Role[]; sectors: Sector[]; skills: Skill[] } | null>(null);

  const [targetRoleId, setTargetRoleId] = useState("");
  const [targetSectorId, setTargetSectorId] = useState("");
  const [preferredRegionId, setPreferredRegionId] = useState("");

  useEffect(() => {
    Promise.all([
      api.get("/students/options"),
      api.get("/students/profile").catch(() => ({ data: null })),
    ]).then(([optRes, profRes]) => {
      setOptions(optRes.data);
      if (profRes.data) setProfile(profRes.data);
      // Prefill from registration
      const rid = localStorage.getItem("selected_region_id");
      if (rid) setPreferredRegionId(rid);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (profile) {
      if (profile.target_role_id) setTargetRoleId(profile.target_role_id);
      if (profile.target_sector_id) setTargetSectorId(profile.target_sector_id);
      if (profile.preferred_region_id) setPreferredRegionId(profile.preferred_region_id);
      if (profile.summary) setSummary(profile.summary);
    }
  }, [profile]);

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      const body: any = {};
      if (targetRoleId) body.target_role_id = targetRoleId;
      if (targetSectorId) body.target_sector_id = targetSectorId;
      if (preferredRegionId) body.preferred_region_id = preferredRegionId;
      if (summary) body.summary = summary;
      await api.put("/students/profile", body);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading…</div>;

  const selectedRole = options?.roles.find((r) => r.id === targetRoleId);
  const selectedSector = options?.sectors.find((s) => s.id === targetSectorId);
  const selectedRegion = options?.regions.find((r) => r.id === preferredRegionId);

  return (
    <div className="mx-auto max-w-2xl">
      <div className="card">
        <div className="card-header">
          <div>
            <h1 className="card-title">Set up your profile</h1>
            <p className="card-sub">Tell us your career target and preferred region</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-navy-600">
            <div className="w-2 h-2 rounded-full bg-accent-400" />
            {user?.full_name}
          </div>
        </div>

        {error && (
          <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 mb-4">{error}</div>
        )}

        <div className="space-y-6">
          <section>
            <label className="block text-sm font-medium text-navy-700 mb-1">Preferred region</label>
            <p className="text-xs text-navy-500 mb-2">Where do you want to work? This drives regional demand.</p>
            <button
              type="button"
              className="input-field flex items-center justify-between text-left cursor-pointer"
              onClick={() => setPreferredRegionId(preferredRegionId ? "" : (options?.regions[0]?.id || ""))}
            >
              {selectedRegion ? (
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-accent-400" />
                  {selectedRegion.name}
                  {selectedRegion.city && <span className="text-navy-400">· {selectedRegion.city}</span>}
                  <span className="text-navy-400">· {selectedRegion.state}</span>
                </span>
              ) : (
                <span className="text-navy-400">Select a region</span>
              )}
            </button>
            <div className="mt-2 grid gap-1">
              {options?.regions.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left transition ${preferredRegionId === r.id ? "border-accent-400 bg-accent-50/30" : "border-surface-line hover:border-navy-200"}`}
                  onClick={() => setPreferredRegionId(r.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: preferredRegionId === r.id ? "#ff6b2c" : "#cbd5e1" }} />
                    <div>
                      <p className="font-medium text-navy-900">{r.name}</p>
                      <p className="text-xs text-navy-500">{r.city} · {r.state}</p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium ${preferredRegionId === r.id ? "text-accent-500" : "text-navy-400"}`}>
                    {preferredRegionId === r.id ? "Selected" : "Select"}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section>
            <label className="block text-sm font-medium text-navy-700 mb-1">Target job role</label>
            <p className="text-xs text-navy-500 mb-2">What role are you aiming for? Demand will be computed for this role.</p>
            <button
              type="button"
              className="input-field flex items-center justify-between text-left cursor-pointer"
              onClick={() => setTargetRoleId(targetRoleId ? "" : (options?.roles[0]?.id || ""))}
            >
              {selectedRole ? selectedRole.name : <span className="text-navy-400">Select a target role</span>}
              <ChevronDown className={`w-4 h-4 text-navy-400 transition-transform ${targetRoleId ? "rotate-180" : ""}`} />
            </button>
            <div className="mt-2 max-h-48 overflow-auto rounded-xl border border-surface-line bg-white">
              {options?.roles.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  className={`w-full text-left px-4 py-3 hover:bg-navy-100 ${targetRoleId === r.id ? "bg-navy-100 font-medium text-navy-900" : "text-navy-700"}`}
                  onClick={() => setTargetRoleId(r.id)}
                >
                  <div className="flex items-center justify-between">
                    <span>{r.name}</span>
                    <span className="text-xs text-navy-400">{r.category}</span>
                  </div>
                  {r.description && <p className="text-xs text-navy-500 ml-4">{r.description}</p>}
                </button>
              ))}
            </div>
          </section>

          <section>
            <label className="block text-sm font-medium text-navy-700 mb-1">Target sector (optional)</label>
            <p className="text-xs text-navy-500 mb-2">Refines demand to a sector like IT, FinTech, Healthcare…</p>
            <button
              type="button"
              className="input-field flex items-center justify-between text-left cursor-pointer"
              onClick={() => setTargetSectorId(targetSectorId ? "" : (options?.sectors[0]?.id || ""))}
            >
              {selectedSector ? selectedSector.name : <span className="text-navy-400">Select a sector</span>}
              <ChevronDown className={`w-4 h-4 text-navy-400 transition-transform ${targetSectorId ? "rotate-180" : ""}`} />
            </button>
            {targetSectorId && (
              <div className="mt-2">
                <p className="text-sm text-navy-700">{selectedSector?.description}</p>
              </div>
            )}
          </section>

          <section>
            <label className="block text-sm font-medium text-navy-700 mb-1">About you (optional)</label>
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="input-field min-h-[100px]"
              placeholder="A short note about your goals, interests, or current focus area."
            />
          </section>

          <div className="flex items-center justify-between pt-2 border-t border-surface-line">
            <div>
              <Link href="/dashboard" className="btn-ghost text-sm">Skip for now</Link>
              <p className="text-xs text-navy-500 mt-1">You can complete this later.</p>
            </div>
            <button
              onClick={save}
              disabled={saving}
              className="btn-primary disabled:opacity-60"
            >
              {saving ? "Saving…" : <><Save className="w-4 h-4" /> Save profile</>}
            </button>
          </div>
        </div>
      </div>

      {/* Quick confirmation strip */}
      {targetRoleId && preferredRegionId && (
        <div className="mt-6 rounded-xl border border-accent-400 bg-accent-50/40 p-4">
          <p className="text-sm font-medium text-accent-700">
            Great — you&apos;re targeting <strong>{selectedRole?.name}</strong> in <strong>{selectedRegion?.name}</strong>.
          </p>
          <p className="text-xs text-accent-600 mt-1">
            Next: add your skills and upload your resume to see your skill gaps.
          </p>
        </div>
      )}
    </div>
  );
}
