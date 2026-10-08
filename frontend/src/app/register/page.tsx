"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { OptionsBucket } from "@/lib/types";
import { api } from "@/lib/api";
import {
  Mail, Lock, User, GraduationCap, Building, MapPin,
  ChevronDown, Plus,
} from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [college, setCollege] = useState("");
  const [department, setDepartment] = useState("");
  const [degree, setDegree] = useState("");
  const [graduationYear, setGraduationYear] = useState("");
  const [location, setLocation] = useState("");

  const [options, setOptions] = useState<OptionsBucket | null>(null);
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [selectedRegionId, setSelectedRegionId] = useState("");
  const [showRolePicker, setShowRolePicker] = useState(false);
  const [showRegionPicker, setShowRegionPicker] = useState(false);

  React.useEffect(() => {
    api.get("/students/options").then((res) => setOptions(res.data)).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await register({
        full_name: fullName,
        email,
        password,
        college,
        department,
        degree,
        graduation_year: graduationYear ? parseInt(graduationYear, 10) : undefined,
        location,
        target_role_id: selectedRoleId || undefined,
      });
      localStorage.setItem("selected_region_id", selectedRegionId || "");
      router.push("/onboarding");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <div className="card">
        <div className="card-header">
          <h1 className="card-title">Create your account</h1>
          <p className="card-sub">Start building your regional skill roadmap</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">{error}</div>
          )}
          <div className="grid gap-4">
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Full name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
                <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-field pl-9" placeholder="Your full name" required />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field pl-9" placeholder="you@college.edu" required />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field pl-9" placeholder="At least 6 characters" required minLength={6} />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">College</label>
            <div className="relative">
              <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
              <input value={college} onChange={(e) => setCollege(e.target.value)} className="input-field pl-9" placeholder="College / university name" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Department</label>
              <input value={department} onChange={(e) => setDepartment(e.target.value)} className="input-field" placeholder="e.g. CSE" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Degree</label>
              <input value={degree} onChange={(e) => setDegree(e.target.value)} className="input-field" placeholder="e.g. B.Tech" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">Graduation year</label>
              <input type="number" value={graduationYear} onChange={(e) => setGraduationYear(e.target.value)} className="input-field" placeholder="2026" min={1990} max={2100} />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-1">City</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
                <input value={location} onChange={(e) => setLocation(e.target.value)} className="input-field pl-9" placeholder="City" list="regions-list" />
                <datalist id="regions-list">
                  {options?.regions.map((r) => (<option key={r.id} value={r.name} />))}
                </datalist>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-navy-700 mb-1">Target job role</label>
            <button
              type="button"
              className="input-field flex items-center justify-between text-left cursor-pointer"
              onClick={() => setShowRolePicker(!showRolePicker)}
            >
              {selectedRoleId ? (
                options?.roles.find((r) => r.id === selectedRoleId)?.name || selectedRoleId
              ) : (
                <span className="text-navy-400">Select a target role (optional)</span>
              )}
              <ChevronDown className={`w-4 h-4 text-navy-400 transition-transform ${showRolePicker ? "rotate-180" : ""}`} />
            </button>
            {showRolePicker && (
              <div className="mt-2 rounded-xl border border-surface-line bg-white shadow-lg max-h-48 overflow-auto">
                {options?.roles.map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    className={`w-full text-left px-4 py-2.5 text-sm hover:bg-navy-100 ${selectedRoleId === r.id ? "bg-navy-100 text-navy-900 font-medium" : "text-navy-700"}`}
                    onClick={() => { setSelectedRoleId(r.id); setShowRolePicker(false); }}
                  >
                    {r.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center disabled:opacity-60"
          >
            {loading ? "Creating account…" : "Create account"}
            <Plus className="w-4 h-4" />
          </button>
        </form>
        <div className="mt-6 text-center text-sm text-navy-600">
          Already have an account?{" "}
          <Link href="/login" className="text-accent-400 font-medium hover:underline">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
