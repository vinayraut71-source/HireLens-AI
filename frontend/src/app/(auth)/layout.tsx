import React from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col justify-center relative overflow-hidden font-sans">
      {/* Background decoration */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-full pointer-events-none overflow-hidden opacity-25 z-0">
        <div className="absolute top-[10%] left-[10%] w-[500px] h-[500px] rounded-full bg-indigo-500/20 blur-[150px]"></div>
        <div className="absolute bottom-[10%] right-[10%] w-[500px] h-[500px] rounded-full bg-emerald-500/20 blur-[150px]"></div>
      </div>

      <div className="relative z-10 flex flex-col justify-center items-center px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <a href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-emerald-400 flex items-center justify-center font-bold text-black text-xl shadow-xl shadow-indigo-500/10 transition-transform group-hover:scale-105">
                HL
              </div>
              <span className="font-bold text-2xl tracking-tight bg-gradient-to-r from-zinc-50 to-zinc-300 bg-clip-text text-transparent">
                HireLens AI
              </span>
            </a>
          </div>

          {/* Children container */}
          {children}
        </div>
      </div>
    </div>
  );
}
