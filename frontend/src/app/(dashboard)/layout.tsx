"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../stores/auth-store";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const auth = useAuthStore();

  useEffect(() => {
    auth.initialize();
  }, []);

  useEffect(() => {
    if (!auth.isLoading && !auth.user) {
      router.push("/login");
    }
  }, [auth.isLoading, auth.user]);

  if (auth.isLoading || !auth.user) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-zinc-400 font-medium animate-pulse">Loading HireLens session...</p>
        </div>
      </div>
    );
  }

  const handleLogout = async () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      try {
        await fetch(`${API_URL}/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch (err) {
        console.error("Failed to logout from server", err);
      }
    }
    auth.logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex font-sans text-zinc-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-900 bg-zinc-950 flex flex-col justify-between hidden md:flex z-10 shrink-0">
        <div>
          {/* Logo */}
          <div className="h-16 flex items-center gap-3 px-6 border-b border-zinc-900">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-emerald-400 flex items-center justify-center font-bold text-black text-sm">
              HL
            </div>
            <span className="font-bold text-base bg-gradient-to-r from-zinc-50 to-zinc-300 bg-clip-text text-transparent">
              HireLens AI
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 flex flex-col gap-1.5">
            <a
              href="/dashboard"
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium bg-zinc-900 text-white transition-colors"
            >
              <span>📊</span> Dashboard
            </a>
            <div className="px-3.5 py-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mt-4">
              Core Loop
            </div>
            <div
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-zinc-650 cursor-not-allowed opacity-50"
              title="Unlocks in Sprint 2"
            >
              <span>📄</span> Resumes
            </div>
            <div
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-zinc-650 cursor-not-allowed opacity-50"
              title="Unlocks in Sprint 4"
            >
              <span>🎯</span> Job Matching
            </div>
            <div
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-zinc-650 cursor-not-allowed opacity-50"
              title="Unlocks in Sprint 5"
            >
              <span>🗺️</span> Learning Roadmaps
            </div>
            <div
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-zinc-650 cursor-not-allowed opacity-50"
              title="Unlocks in Sprint 6"
            >
              <span>📁</span> Applications
            </div>
            <div className="px-3.5 py-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mt-4">
              System
            </div>
            <div
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-zinc-650 cursor-not-allowed opacity-50"
              title="Unlocks in Sprint 6"
            >
              <span>🕵️‍♂️</span> Activity Log
            </div>
          </nav>
        </div>

        {/* User profile section at the bottom */}
        <div className="p-4 border-t border-zinc-900 flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-zinc-300 shrink-0">
              {auth.user.full_name[0].toUpperCase()}
            </div>
            <div className="overflow-hidden">
              <div className="text-sm font-semibold text-white truncate">{auth.user.full_name}</div>
              <div className="text-xs text-zinc-500 capitalize truncate">{auth.user.plan_tier} Plan</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer"
            title="Log Out"
          >
            ❌
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Mobile Header */}
        <header className="h-16 border-b border-zinc-900 bg-zinc-950 flex items-center justify-between px-6 md:hidden z-10">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-emerald-400 flex items-center justify-center font-bold text-black text-sm">
              HL
            </div>
            <span className="font-bold text-base text-white">HireLens AI</span>
          </div>
          <button
            onClick={handleLogout}
            className="text-xs text-zinc-400 hover:text-zinc-200 cursor-pointer bg-zinc-900 px-3 py-1.5 rounded-lg border border-zinc-850"
          >
            Log Out
          </button>
        </header>

        {/* Dynamic children content */}
        <main className="flex-1 overflow-y-auto bg-zinc-950 text-zinc-100 p-6 sm:p-8 relative">
          {/* Background decoration */}
          <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none z-0"></div>
          <div className="relative z-10">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
