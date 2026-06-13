import Image from "next/image";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-indigo-500 selection:text-white overflow-x-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] pointer-events-none overflow-hidden opacity-30">
        <div className="absolute top-[-200px] left-[-200px] w-[600px] h-[600px] rounded-full bg-indigo-500 blur-[150px]"></div>
        <div className="absolute top-[-100px] right-[-100px] w-[500px] h-[500px] rounded-full bg-emerald-500 blur-[150px]"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-emerald-400 flex items-center justify-center font-bold text-black text-lg shadow-lg shadow-indigo-500/20">
              HL
            </div>
            <span className="font-semibold text-lg tracking-tight bg-gradient-to-r from-zinc-50 to-zinc-300 bg-clip-text text-transparent">
              HireLens AI
            </span>
          </div>
          <nav className="flex items-center gap-4">
            <a href="/login" className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors">
              Sign In
            </a>
            <a
              href="/register"
              className="text-sm font-medium bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 px-4 h-9 flex items-center rounded-lg transition-colors"
            >
              Get Started
            </a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-16 text-center lg:text-left lg:pt-32 lg:pb-24">
        <div className="grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 flex flex-col gap-6">
            <div className="inline-flex self-center lg:self-start items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-400 text-xs font-semibold tracking-wide">
              <span>🚀</span> Sprint 0 Scaffold Complete
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.1]">
              Your AI-powered <br />
              <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-emerald-400 bg-clip-text text-transparent">
                Career Copilot
              </span>
            </h1>
            <p className="text-lg text-zinc-400 max-w-2xl leading-relaxed">
              HireLens AI guides you from resume optimization through interview prep and application tracking. Combining semantic analysis, ATS scoring, and automated skill-gap learning roadmaps.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-4">
              <a
                href="/register"
                className="w-full sm:w-auto h-12 px-6 rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white font-semibold flex items-center justify-center shadow-lg shadow-indigo-500/20 transition-all hover:scale-[1.02]"
              >
                Create Free Account
              </a>
              <a
                href="#features"
                className="w-full sm:w-auto h-12 px-6 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 text-zinc-300 font-medium flex items-center justify-center transition-colors"
              >
                Explore Features
              </a>
            </div>
          </div>
          <div className="lg:col-span-5 flex justify-center">
            {/* Visual placeholder box showcasing modern CSS/Glassmorphism */}
            <div className="w-full max-w-[400px] aspect-[4/3] rounded-2xl border border-zinc-800/80 bg-zinc-900/40 backdrop-blur-sm p-6 flex flex-col justify-between shadow-2xl relative overflow-hidden">
              <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-indigo-500/10 rounded-full blur-2xl"></div>
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <span className="text-xs text-zinc-500 font-mono">resume_v3.pdf</span>
              </div>
              <div className="flex-1 py-6 flex flex-col gap-4 justify-center">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-400">ATS Match Score</span>
                  <span className="text-xl font-bold text-emerald-400">91%</span>
                </div>
                <div className="w-full bg-zinc-800 h-2.5 rounded-full overflow-hidden">
                  <div className="bg-emerald-400 h-full rounded-full" style={{ width: "91%" }}></div>
                </div>
                <p className="text-xs text-zinc-500 italic">
                  "Quantified metrics added to 3 bullets; Kubernetes and CI/CD added to skills."
                </p>
              </div>
              <div className="border-t border-zinc-800/80 pt-4 flex justify-between items-center text-xs text-zinc-400">
                <span>Status: Ready</span>
                <span className="text-indigo-400">View Feedback →</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-6 py-24 border-t border-zinc-900">
        <div className="text-center max-w-3xl mx-auto mb-16 flex flex-col gap-4">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Core Career Intelligence Loop
          </h2>
          <p className="text-zinc-400">
            A comprehensive, modular environment supporting your journey from initial application to final offer.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Card 1 */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col gap-4 hover:border-zinc-850 hover:bg-zinc-900/40 transition-all">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 font-bold">
              📄
            </div>
            <h3 className="text-lg font-semibold text-white">Resume Versioning</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Create immutable snapshots on upload or edit. Track your ATS score progression and optimize per-role.
            </p>
          </div>

          {/* Card 2 */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col gap-4 hover:border-zinc-850 hover:bg-zinc-900/40 transition-all">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 font-bold">
              📊
            </div>
            <h3 className="text-lg font-semibold text-white">ATS Scoring</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Get detailed section-level parsing reviews, keyword counts, and tailoring metrics using Gemini.
            </p>
          </div>

          {/* Card 3 */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col gap-4 hover:border-zinc-850 hover:bg-zinc-900/40 transition-all">
            <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center text-violet-400 font-bold">
              🎯
            </div>
            <h3 className="text-lg font-semibold text-white">Job Matching</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Generate local embeddings and run similarity search using FAISS for semantic title and description alignment.
            </p>
          </div>

          {/* Card 4 */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col gap-4 hover:border-zinc-850 hover:bg-zinc-900/40 transition-all">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 font-bold">
              🗺️
            </div>
            <h3 className="text-lg font-semibold text-white">Learning Roadmaps</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Close detected skill gaps with tailored modules, study hours, project concepts, and resource links.
            </p>
          </div>

          {/* Card 5 */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col gap-4 hover:border-zinc-850 hover:bg-zinc-900/40 transition-all">
            <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400 font-bold">
              📁
            </div>
            <h3 className="text-lg font-semibold text-white">Application Pipeline</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Monitor your job search pipeline using our 7-stage status kanban interface and analytics reports.
            </p>
          </div>

          {/* Card 6 */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-900/20 p-6 flex flex-col gap-4 hover:border-zinc-850 hover:bg-zinc-900/40 transition-all">
            <div className="w-10 h-10 rounded-lg bg-teal-500/10 flex items-center justify-center text-teal-400 font-bold">
              🕵️‍♂️
            </div>
            <h3 className="text-lg font-semibold text-white">Human-in-the-Loop</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Tailor resume packages and drafts. Review and authorize before finalizing any submission details.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-zinc-900/80 bg-zinc-950 py-12 text-center text-sm text-zinc-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-6">
          <p>© 2026 HireLens AI. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-zinc-300">Privacy Policy</a>
            <a href="#" className="hover:text-zinc-300">Terms of Service</a>
            <a href="#" className="hover:text-zinc-300">Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
