"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Roadmap, RoadmapItem, Skill } from "@/lib/types";
import {
  Clock, Check, Play, CircleDot, GitBranch, Link, ExternalLink,
  ChevronDown, ChevronRight, Trophy, FileText, Zap,
} from "lucide-react";
import { cn, formatPercent } from "@/lib/utils";

export default function RoadmapPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [generating, setGenerating] = useState(false);
  const [expandedItem, setExpandedItem] = useState<string | null>(null);

  useEffect(() => {
    api.get("/roadmap").then((res) => {
      setRoadmap(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const generate = async () => {
    setGenerating(true);
    try {
      const profileRes = await api.get("/students/profile");
      const body: any = { user_id: user?.id };
      if (profileRes.data?.target_role_id) body.role_id = profileRes.data.target_role_id;
      if (profileRes.data?.preferred_region_id) body.region_id = profileRes.data.preferred_region_id;
      if (profileRes.data?.target_sector_id) body.sector_id = profileRes.data.target_sector_id;
      const res = await api.post("/roadmap/generate", body);
      setRoadmap(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Could not generate roadmap");
    } finally {
      setGenerating(false);
    }
  };

  const updateItem = async (itemId: string, patch: any) => {
    try {
      const res = await api.put(`/roadmap/items/${itemId}`, patch);
      setRoadmap((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map((i) => (i.id === itemId ? res.data : i)),
        };
      });
    } catch {}
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading roadmap…</div>;

  const items = roadmap?.items || [];

  const overallProgress = items.length ? Math.round((items.filter((i) => i.status === "completed").length / items.length) * 100) : 0;

  const stagesDone = (item: RoadmapItem) => {
    let n = 0;
    if (item.learn_status === "completed") n++;
    if (item.build_status === "completed") n++;
    if (item.prove_status === "completed") n++;
    return n;
  };

  return (
    <div>
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-navy-900 flex items-center gap-2">
              <Clock className="w-6 h-6 text-accent-400" /> Your roadmap
            </h1>
            <p className="text-sm text-navy-600 mt-1">
              {roadmap?.title || "Generate a roadmap from your profile."}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={generate} disabled={generating} className="btn-secondary text-sm disabled:opacity-50">
              <Zap className="w-4 h-4" /> {generating ? "Generating…" : "Regenerate"}
            </button>
          </div>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="card">
          <div className="py-12 text-center">
            <Clock className="w-10 h-10 text-navy-300 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-navy-900">No roadmap yet</h2>
            <p className="text-sm text-navy-600 mt-1 max-w-md mx-auto">
              Generate a personalized 6-week roadmap based on your profile, target role, and regional demand.
            </p>
            <button onClick={generate} disabled={generating} className="btn-primary mt-6">
              <Zap className="w-4 h-4" /> {generating ? "Generating…" : "Generate roadmap"}
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Progress strip */}
          <div className="card mb-6">
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-navy-900">{overallProgress}%</p>
                <p className="text-xs text-navy-500">complete</p>
              </div>
              <div className="h-2 w-px bg-surface-line" />
              <div className="flex-1">
                <div className="h-2 rounded-full bg-navy-200 overflow-hidden">
                  <div className="h-full rounded-full bg-accent-400 transition-all duration-500" style={{ width: `${overallProgress}%` }} />
                </div>
                <p className="text-xs text-navy-500 mt-1">{items.filter((i) => i.status === "completed").length} of {items.length} weeks done</p>
              </div>
              <div className="text-right text-sm text-navy-600">
                {items.filter((i) => i.learn_status === "completed").length} learn ·
                {items.filter((i) => i.build_status === "completed").length} build ·
                {items.filter((i) => i.prove_status === "completed").length} prove
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="relative">
            <div className="absolute left-5 top-2 bottom-2 w-0.5 bg-surface-line" />
            <div className="space-y-4">
              {items.map((item) => (
                <div key={item.id} className={cn("relative pl-12", expandedItem === item.id && "pb-4")}>
                  <div className="card mb-2 flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "flex h-10 w-10 items-center justify-center rounded-full shrink-0 border-2",
                        item.status === "completed" && "bg-emerald-50 border-emerald-400",
                        item.status === "in_progress" && "bg-accent-50 border-accent-400",
                        item.status === "blocked" && "bg-red-50 border-red-400",
                        item.status === "pending" && "bg-navy-100 border-navy-300",
                      )}>
                        {item.status === "completed" && <Check className="w-5 h-5 text-emerald-600" />}
                        {item.status === "in_progress" && <Play className="w-5 h-5 text-accent-500 fill-accent-400" />}
                        {item.status === "blocked" && <CircleDot className="w-5 h-5 text-red-500" />}
                        {item.status === "pending" && <span className="text-xs font-bold text-navy-500">W{item.week_number}</span>}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-navy-900">Week {item.week_number}: {item.title}</h3>
                          {item.skill && <span className="skill-pill skill-pill-neutral text-xs">{item.skill.name}</span>}
                          <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full", item.status === "completed" && "bg-emerald-50 text-emerald-700", item.status === "in_progress" && "bg-accent-50 text-accent-700", item.status === "pending" && "bg-navy-100 text-navy-600")}>
                            {item.status}
                          </span>
                        </div>
                        <p className="text-sm text-navy-600 mt-0.5">{item.learning_objective}</p>
                      </div>
                    </div>
                    <button
                      className="btn-ghost text-xs"
                      onClick={() => setExpandedItem(expandedItem === item.id ? null : item.id)}
                    >
                      {expandedItem === item.id ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      <span className="ml-1">Details</span>
                    </button>
                  </div>

                  {expandedItem === item.id && (
                    <div className="ml-11 rounded-xl border border-surface-line bg-white p-4 space-y-4">
                      <div className="grid sm:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs font-medium text-navy-500 uppercase tracking-wider mb-1">LEARN</p>
                          <p className="text-sm text-navy-700">{item.learning_objective}</p>
                          <label className="flex items-center gap-2 mt-3">
                            <select
                              value={item.learn_status}
                              onChange={(e) => updateItem(item.id, { learn_status: e.target.value })}
                              className="text-xs rounded border border-surface-line bg-white px-2 py-1"
                            >
                              <option value="pending">Not started</option>
                              <option value="in_progress">In progress</option>
                              <option value="completed">Completed</option>
                            </select>
                            <span className={cn("text-xs", item.learn_status === "completed" ? "text-emerald-600" : "text-navy-500")}>
                              {item.learn_status === "completed" ? <><Check className="w-3 h-3 inline" /> Done</> : item.learn_status}
                            </span>
                          </label>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-navy-500 uppercase tracking-wider mb-1">BUILD</p>
                          <p className="text-sm text-navy-700">{item.project_task}</p>
                          <label className="flex items-center gap-2 mt-3">
                            <select
                              value={item.build_status}
                              onChange={(e) => updateItem(item.id, { build_status: e.target.value })}
                              className="text-xs rounded border border-surface-line bg-white px-2 py-1"
                            >
                              <option value="pending">Not started</option>
                              <option value="in_progress">In progress</option>
                              <option value="completed">Completed</option>
                            </select>
                            <span className={cn("text-xs", item.build_status === "completed" ? "text-emerald-600" : "text-navy-500")}>
                              {item.build_status === "completed" ? <><Check className="w-3 h-3 inline" /> Done</> : item.build_status}
                            </span>
                          </label>
                        </div>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-navy-500 uppercase tracking-wider mb-1">PROVE</p>
                        <div className="flex items-start gap-3">
                          <label className="flex-1 flex items-center gap-2">
                            <input
                              type="text"
                              value={item.project?.github_url || ""}
                              onChange={(e) => updateItem(item.id, { project_id: "" })}
                              placeholder="GitHub URL"
                              className="input-field text-xs flex-1"
                            />
                          </label>
                          <span className="text-xs text-navy-500">{item.project?.github_url ? <><ExternalLink className="w-3 h-3 inline" /> Linked</> : "No link"}</span>
                        </div>
                        <div className="mt-2 flex items-center gap-2">
                          <input
                            type="text"
                            value={item.project?.demo_url || ""}
                            onChange={(e) => updateItem(item.id, { project_id: "" })}
                            placeholder="Demo URL (optional)"
                            className="input-field text-xs flex-1"
                          />
                        </div>
                        <div className="flex items-center gap-2 text-xs text-navy-500 mt-2">
                          <FileText className="w-3.5 h-3.5" />
                          <span>Proof: {item.expected_output || "Complete the project task and attach proof."}</span>
                        </div>
                        <label className="flex items-center gap-2 mt-2">
                          <span>Prove status:</span>
                          <select
                            value={item.prove_status}
                            onChange={(e) => updateItem(item.id, { prove_status: e.target.value })}
                            className="text-xs rounded border border-surface-line bg-white px-2 py-1"
                          >
                            <option value="pending">Pending</option>
                            <option value="in_progress">In progress</option>
                            <option value="completed">Completed</option>
                          </select>
                        </label>
                      </div>

                      <div className="flex items-center gap-2 pt-2 border-t border-surface-line">
                        <button
                          onClick={() => updateItem(item.id, { status: item.status === "completed" ? "pending" : "completed" })}
                          className="btn-secondary text-xs"
                        >
                          {item.status === "completed" ? "Mark incomplete" : "Mark week complete"}
                        </button>
                        {item.project?.github_url && (
                          <a href={item.project.github_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs flex items-center gap-1">
                            <ExternalLink className="w-3 h-3" /> GitHub
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Learn → Build → Prove concept */}
          <div className="card mt-6">
            <div className="card-header">
              <h2 className="card-title flex items-center gap-2"><GitBranch className="w-4 h-4 text-navy-500" /> How to use this roadmap</h2>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-navy-600">
              <div className="flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-navy-600 text-white text-xs flex items-center justify-center font-medium">1</span> Learn the concept</div>
              <ArrowRightIcon className="w-4 h-4 text-navy-400" />
              <div className="flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-accent-400 text-white text-xs flex items-center justify-center font-medium">2</span> Build the project</div>
              <ArrowRightIcon className="w-4 h-4 text-navy-400" />
              <div className="flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-navy-600 text-white text-xs flex items-center justify-center font-medium">3</span> Prove with proof (GitHub/demo/screenshot)</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}
