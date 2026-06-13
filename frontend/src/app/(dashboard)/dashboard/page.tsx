"use client";

import React from "react";
import { useAuthStore } from "../../../stores/auth-store";

export default function DashboardPage() {
  const auth = useAuthStore();

  return (
    <div className="flex flex-col gap-8">
      {/* Header section */}
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-sans">Dashboard</h1>
        <p className="text-sm text-zinc-400">Welcome to your Career Copilot workspace</p>
      </div>

      {/* Welcome banner */}
      <div className="rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-500/10 via-violet-500/5 to-zinc-950 p-6 sm:p-8 flex flex-col gap-4 relative overflow-hidden">
        <div className="absolute right-0 top-0 h-full w-[200px] bg-gradient-to-l from-indigo-500/5 to-transparent blur-xl pointer-events-none"></div>
        <div className="flex flex-col gap-2 relative z-10">
          <div className="inline-flex self-start px-2.5 py-0.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-400 text-xs font-semibold">
            Sprint 1 Scaffold Ready
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">
            Welcome back, {auth.user?.full_name}!
          </h2>
          <p className="text-zinc-400 text-sm sm:text-base max-w-2xl leading-relaxed">
            Your secure career profile is authenticated. In subsequent sprints, you will be able to upload your resumes, calculate ATS scores, match jobs, generate personalized learning plans, and track your interview pipeline.
          </p>
        </div>
      </div>

      {/* Grid of stats */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Card 1: Resume */}
        <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-5 flex flex-col gap-3 relative overflow-hidden">
          <div className="text-sm font-semibold text-zinc-400">Resumes</div>
          <div className="text-2xl font-bold text-white">0</div>
          <div className="text-xs text-zinc-500">Unlocks in Sprint 2</div>
        </div>

        {/* Card 2: ATS Score */}
        <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-5 flex flex-col gap-3 relative overflow-hidden">
          <div className="text-sm font-semibold text-zinc-400">ATS Score (Avg)</div>
          <div className="text-2xl font-bold text-zinc-650">—</div>
          <div className="text-xs text-zinc-500">Unlocks in Sprint 3</div>
        </div>

        {/* Card 3: Job Matches */}
        <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-5 flex flex-col gap-3 relative overflow-hidden">
          <div className="text-sm font-semibold text-zinc-400">Job Matches</div>
          <div className="text-2xl font-bold text-zinc-650">—</div>
          <div className="text-xs text-zinc-500">Unlocks in Sprint 4</div>
        </div>

        {/* Card 4: Applications */}
        <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-5 flex flex-col gap-3 relative overflow-hidden">
          <div className="text-sm font-semibold text-zinc-400">Applications</div>
          <div className="text-2xl font-bold text-white">0</div>
          <div className="text-xs text-zinc-500">Unlocks in Sprint 6</div>
        </div>
      </div>

      {/* Action panel placeholders */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-zinc-900 bg-zinc-900/10 p-6 flex flex-col gap-4">
          <h3 className="text-lg font-semibold text-white">Next Steps</h3>
          <div className="flex flex-col gap-3">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-zinc-900/40 border border-zinc-900">
              <span className="text-lg">📄</span>
              <div className="flex flex-col gap-0.5">
                <span className="text-sm font-semibold text-white">Upload your Resume</span>
                <span className="text-xs text-zinc-500">Sprint 2 parser will support PDF and DOCX extractions.</span>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-zinc-900/40 border border-zinc-900">
              <span className="text-lg">🎯</span>
              <div className="flex flex-col gap-0.5">
                <span className="text-sm font-semibold text-white">Evaluate Job Match</span>
                <span className="text-xs text-zinc-500">Sprint 4 will introduce FAISS similarity semantic checks.</span>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-900 bg-zinc-900/10 p-6 flex flex-col gap-4">
          <h3 className="text-lg font-semibold text-white">Active Plan</h3>
          <div className="flex flex-col gap-2">
            <div className="text-sm font-semibold text-indigo-400 capitalize">{auth.user?.plan_tier} Tier</div>
            <p className="text-xs text-zinc-500 leading-relaxed">
              You are currently utilizing the free access tier of HireLens. Upgrades are available under future Sprint roadmaps.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
