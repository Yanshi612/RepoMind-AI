import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";

const FEATURES = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
      </svg>
    ),
    color: "#3b82f6",
    title: "Instant Indexing",
    desc:  "Shallow-clone any GitHub repo in seconds with smart binary filtering and async processing.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a10 10 0 1 1 0 20A10 10 0 0 1 12 2z"/>
        <path d="M12 8v4l3 3"/>
      </svg>
    ),
    color: "#8b5cf6",
    title: "AI-Powered Q&A",
    desc:  "Ask natural-language questions about any function, pattern, or architecture decision.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
    ),
    color: "#06b6d4",
    title: "Scoped & Precise",
    desc:  "Queries are isolated per-repository — no cross-contamination, always on-point answers.",
  },
];

const STATS = [
  { value: "500+",  label: "Repos Analyzed"  },
  { value: "10M+",  label: "Lines Indexed"   },
  { value: "< 60s", label: "Avg Analysis"    },
  { value: "100%",  label: "Open Source"     },
];

function Footer() {
  return (
    <p className="text-center text-xs py-8" style={{ color: "#334155" }}>
      Powered by RepoMind AI · Built with ♥ · 2025
    </p>
  );
}

function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#07080f", color: "#f1f5f9" }}>
      <Navbar />

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 pt-28 pb-24 overflow-hidden">

        {/* Glow blobs */}
        <div className="blob w-96 h-96 -top-20 -left-20" style={{ background: "#3b82f6" }} />
        <div className="blob w-80 h-80 top-10 right-0"  style={{ background: "#8b5cf6" }} />

        {/* Badge */}
        <div className="fade-up inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-8 text-xs font-medium"
             style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.25)", color: "#60a5fa" }}>
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          AI-powered code intelligence
        </div>

        {/* Headline */}
        <h1 className="fade-up text-5xl md:text-7xl font-black tracking-tight leading-tight max-w-3xl"
            style={{ animationDelay: "0.05s" }}>
          Understand Any{" "}
          <span className="gradient-text">Codebase</span>
          <br />Instantly
        </h1>

        {/* Sub */}
        <p className="fade-up mt-6 text-lg max-w-xl leading-relaxed"
           style={{ color: "#64748b", animationDelay: "0.1s" }}>
          RepoMind AI indexes GitHub repositories in seconds and lets you ask
          natural-language questions about architecture, functions, and code patterns.
        </p>

        {/* CTAs */}
        <div className="fade-up flex flex-col sm:flex-row gap-4 mt-10"
             style={{ animationDelay: "0.15s" }}>
          <button
            id="hero-cta-primary"
            onClick={() => navigate("/repository")}
            className="px-8 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 hover:opacity-90 hover:scale-105"
            style={{ background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", color: "#fff" }}
          >
            Analyze a Repository →
          </button>
          <button
            id="hero-cta-secondary"
            onClick={() => navigate("/dashboard")}
            className="px-8 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 hover:bg-white/5"
            style={{ border: "1px solid rgba(255,255,255,0.1)", color: "#94a3b8" }}
          >
            View Dashboard
          </button>
        </div>
      </section>

      {/* ── Stats ────────────────────────────────────────────── */}
      <section className="px-6 pb-16">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map(({ value, label }) => (
            <div key={label}
                 className="rounded-2xl p-6 text-center transition-all duration-200 hover:scale-105"
                 style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}>
              <p className="text-3xl font-black gradient-text">{value}</p>
              <p className="text-xs mt-1" style={{ color: "#475569" }}>{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section className="px-6 pb-24">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-center text-2xl font-bold mb-2">Everything you need</h2>
          <p className="text-center text-sm mb-10" style={{ color: "#64748b" }}>
            Built for developers who want to understand code fast.
          </p>

          <div className="grid md:grid-cols-3 gap-5">
            {FEATURES.map(({ icon, color, title, desc }) => (
              <div key={title}
                   className="rounded-2xl p-7 transition-all duration-300 hover:scale-[1.02]"
                   style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-5"
                     style={{ background: `${color}18`, color }}>
                  {icon}
                </div>
                <h3 className="font-semibold text-base mb-2">{title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: "#64748b" }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Bottom CTA ───────────────────────────────────────── */}
      <section className="px-6 pb-20">
        <div className="max-w-2xl mx-auto rounded-2xl p-12 text-center"
             style={{ background: "linear-gradient(135deg,rgba(59,130,246,0.12),rgba(139,92,246,0.12))",
                      border: "1px solid rgba(139,92,246,0.2)" }}>
          <h2 className="text-3xl font-bold mb-3">Ready to explore your codebase?</h2>
          <p className="text-sm mb-8" style={{ color: "#64748b" }}>
            Paste a GitHub URL and get AI insights in under a minute.
          </p>
          <button
            id="bottom-cta-btn"
            onClick={() => navigate("/repository")}
            className="px-10 py-4 rounded-xl font-semibold text-sm transition-all duration-200 hover:opacity-90 hover:scale-105"
            style={{ background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", color: "#fff" }}
          >
            Get Started — It's Free
          </button>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default Home;
