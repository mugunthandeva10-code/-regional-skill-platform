"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { ArrowRight, Target, MapPin, BookOpen, TrendingUp, CircleCheck } from "lucide-react";

export default function LandingPage() {
  const { user, loading } = useAuth();

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]">Loading…</div>;

  if (user?.role === "student") {
    return <div className="flex items-center justify-center min-h-[60vh]"><Link href="/dashboard" className="btn-primary text-base px-6 py-3">Go to Dashboard →</Link></div>;
  }

  if (user?.role === "admin") {
    return <div className="flex items-center justify-center min-h-[60vh]"><Link href="/admin" className="btn-primary text-base px-6 py-3">Go to Admin</Link></div>;
  }

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-navy-900 text-white">
        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-accent-400/30 via-transparent to-transparent" />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 sm:py-28">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 text-accent-400 text-sm font-medium tracking-wide uppercase mb-4">
              <span className="w-2 h-2 rounded-full bg-accent-400" />
              Decision-support for students
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight tracking-tight">
              Know what skills your market needs.
              <br />
              Know what you&apos;re missing.
              <br />
              Know what to build next.
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-navy-200 max-w-2xl leading-relaxed">
              A regional skill intelligence platform that connects employer demand in your city with
              your current skills, finds your gaps, explains why they matter, and generates a personal
              six-week roadmap with real project proof.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-4">
              <Link href="/register" className="btn-primary bg-accent-400 hover:bg-accent-500 px-6 py-3 text-base shadow-lg shadow-accent-400/20">
                Build my skill roadmap
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link href="/login" className="btn-secondary bg-white/10 border-white/20 text-white hover:bg-white/20 px-6 py-3 text-base">
                Sign in
              </Link>
            </div>
          </div>
        </div>
        {/* decorative cards on hero bottom */}
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-16 sm:pb-24">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-white/10 border border-white/10 p-5 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-accent-400 text-sm font-medium mb-2">
                <MapPin className="w-4 h-4" /> Regional demand
              </div>
              <p className="text-white font-semibold text-lg">10 roles × 5 cities</p>
              <p className="text-navy-300 text-sm mt-1">Computed from structured job data</p>
            </div>
            <div className="rounded-2xl bg-white/10 border border-white/10 p-5 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-accent-400 text-sm font-medium mb-2">
                <Target className="w-4 h-4" /> Skill gaps
              </div>
              <p className="text-white font-semibold text-lg">Matched / Partial / Missing</p>
              <p className="text-navy-300 text-sm mt-1">Priority-scored with reasons</p>
            </div>
            <div className="rounded-2xl bg-white/10 border border-white/10 p-5 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-accent-400 text-sm font-medium mb-2">
                <BookOpen className="w-4 h-4" /> Personal roadmap
              </div>
              <p className="text-white font-semibold text-lg">6-week LEARN → BUILD → PROVE</p>
              <p className="text-navy-300 text-sm mt-1">With project proof tracking</p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-navy-900">How it works</h2>
            <p className="mt-3 text-navy-600 max-w-2xl mx-auto">
              From regional market data to your personal next project — in six weeks.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {steps.map((s, i) => (
              <div key={s.title} className="card card-grid border-l-4 border-l-accent-400 pl-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-400 text-white text-sm font-bold">
                    {i + 1}
                  </span>
                  <h3 className="font-semibold text-navy-900">{s.title}</h3>
                </div>
                <p className="text-sm text-navy-600">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-navy-100">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-navy-900">What you get</h2>
            <p className="mt-3 text-navy-600 max-w-2xl mx-auto">
              Not a job portal. Not a chatbot. A decision-support system between regional demand and your next move.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div key={f.title} className="card flex gap-4">
                <div className="mt-1 text-accent-400">{f.icon}</div>
                <div>
                  <h3 className="font-semibold text-navy-900">{f.title}</h3>
                  <p className="text-sm text-navy-600 mt-1">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-navy-800 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold">Ready to close your skill gaps?</h2>
          <p className="mt-3 text-navy-300 max-w-xl mx-auto">
            Register as a student, pick Chennai and Backend Developer, add your skills, and see your
            personalized roadmap in under five minutes.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4">
            <Link href="/register" className="btn-primary bg-accent-400 hover:bg-accent-500 px-6 py-3 text-base shadow-lg shadow-accent-400/20">
              Build my skill roadmap
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="/login" className="btn-secondary bg-white/10 border-white/20 text-white hover:bg-white/20 px-6 py-3 text-base">
              Student demo login
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

const steps = [
  { title: "Regional job data", desc: "Skill demand is computed from curated job postings across Chennai, Coimbatore, Bengaluru, Hyderabad, and Pune." },
  { title: "Skill extraction & normalization", desc: "Resume text is parsed and skills are normalized to a central taxonomy (AWS, REST APIs, Spring Boot, Docker…)." },
  { title: "Regional demand engine", desc: "Demand scores are calculated from the data you have — frequency, recency, role relevance, sector relevance — fully configurable." },
  { title: "Skill gap analysis", desc: "Your skills are compared against market demand and classified as Matched, Partial, or Missing." },
  { title: "Priority & explanation", desc: "Gaps are ranked with a transparent score and an honest explanation of why each one matters for your target role." },
  { title: "Personal roadmap & proof", desc: "A six-week LEARN → BUILD → PROVE roadmap with projects and proof (GitHub, demo link, screenshots)." },
];

const features = [
  { icon: <Target className="w-6 h-6" />, title: "Regional demand", desc: "See what your region and target role actually require, with demand %, evidence, and confidence." },
  { icon: <CircleCheck className="w-6 h-6" />, title: "Skill gap clarity", desc: "Matched, partial, and missing skills compared against market demand — sorted by priority." },
  { icon: <TrendingUp className="w-6 h-6" />, title: "Explainable priority", desc: "Every recommendation answers “why this, why now” with demand, gap, and your current level." },
  { icon: <BookOpen className="w-6 h-6" />, title: "6-week roadmap", desc: "A personalized roadmap with learning objectives, practice tasks, and project tasks." },
  { icon: <MapPin className="w-6 h-6" />, title: "City fallback", desc: "Small cities fall back to district/state/region data with a clear confidence indicator — never hidden." },
  { icon: <CircleCheck className="w-6 h-6" />, title: "Project proof", desc: "Attach GitHub, demo links, and screenshots to prove each skill to employers." },
];
