import { normalizeRepoUrl } from "../utils/normalizeRepoUrl";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";

/* ─── Helpers ────────────────────────────────────────────────── */

function timeAgo(isoString) {
  if (!isoString) return "Unknown";
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins  < 1)  return "Just now";
  if (mins  < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

function shortName(url = "") {
  const value = normalizeRepoUrl(url);
  return value.replace("https://github.com/", "").replace(/\.git$/, "") || value;
}

/* ─── Component ──────────────────────────────────────────────── */

function RecentScans() {
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);

  /* Load from localStorage on mount */
  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem("recentScans") || "[]");
      // Newest first
      setScans([...stored].reverse());
    } catch {
      setScans([]);
    }
  }, []);

  /* Load a past scan as the active repo and navigate to dashboard */
  const loadScan = (scan) => {
    localStorage.setItem("repositoryAnalysis", JSON.stringify(scan));
    navigate("/dashboard");
  };

  /* Delete a single scan from history */
  const deleteScan = (e, index) => {
    e.stopPropagation();
    const stored   = JSON.parse(localStorage.getItem("recentScans") || "[]");
    const reversed = [...stored].reverse();
    reversed.splice(index, 1);
    const updated  = [...reversed].reverse();
    localStorage.setItem("recentScans", JSON.stringify(updated));
    setScans(reversed.filter((_, i) => i !== index));
  };

  /* Clear all history */
  const clearAll = () => {
    localStorage.removeItem("recentScans");
    setScans([]);
  };

  return (
    <div className="flex min-h-screen" style={{ background: "#07080f", color: "#f1f5f9" }}>
      <Sidebar />

      <main className="flex-1 flex flex-col p-8 md:p-12 overflow-auto">
        <div className="max-w-3xl w-full mx-auto flex-1 flex flex-col gap-7">

          {/* Header */}
          <div className="fade-up flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Recent Scans</h1>
              <p className="mt-1.5 text-sm" style={{ color: "#64748b" }}>
                {scans.length} repositor{scans.length === 1 ? "y" : "ies"} previously analyzed
              </p>
            </div>
            {scans.length > 0 && (
              <button
                onClick={clearAll}
                className="px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 hover:opacity-80"
                style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171" }}>
                Clear All
              </button>
            )}
          </div>

          {/* Empty state */}
          {scans.length === 0 && (
            <div className="rounded-2xl p-14 text-center fade-up"
                 style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}>
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
                   style={{ background: "rgba(59,130,246,0.1)", color: "#3b82f6" }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2">No Scans Yet</h2>
              <p className="text-sm mb-7" style={{ color: "#64748b" }}>
                Analyze a GitHub repository to see your scan history here.
              </p>
              <button
                onClick={() => navigate("/repository")}
                className="px-7 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:opacity-90"
                style={{ background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", color: "#fff" }}>
                Analyze First Repository
              </button>
            </div>
          )}

          {/* Scan list */}
          {scans.length > 0 && (
            <div className="flex flex-col gap-3 fade-up">
              {scans.map((scan, i) => {
                const name   = shortName(scan.repo_url);
                const files  = scan.stats?.total_files ?? "—";
                const chunks = scan.vector_db?.chunks_stored ?? scan.vector_db?.chunks ?? 0;
                const lang   = scan.stats?.python_files > 0 ? "Python"
                             : scan.stats?.javascript_files > 0 ? "JavaScript"
                             : scan.stats?.typescript_files > 0 ? "TypeScript"
                             : "Mixed";

                return (
                  <div
                    key={i}
                    onClick={() => loadScan(scan)}
                    className="group rounded-2xl p-6 cursor-pointer transition-all duration-200 hover:scale-[1.01]"
                    style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <div className="flex items-start justify-between gap-4">

                      {/* Left: repo info */}
                      <div className="flex items-center gap-4 min-w-0">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                             style={{ background: "linear-gradient(135deg,#3b82f6,#8b5cf6)" }}>
                          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M7 8l-4 4 4 4"/><path d="M17 8l4 4-4 4"/><path d="M14 4l-4 16"/>
                          </svg>
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-sm truncate">{name}</p>
                          <p className="text-xs mt-0.5 truncate" style={{ color: "#475569" }}>
                            {scan.repo_url}
                          </p>
                        </div>
                      </div>

                      {/* Right: actions */}
                      <div className="flex items-center gap-3 shrink-0">
                        <button
                          onClick={(e) => deleteScan(e, i)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-white/5"
                          style={{ color: "#475569" }}
                          title="Remove">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>
                          </svg>
                        </button>
                        <span className="text-xs px-2 py-1 rounded-md"
                              style={{ background: "rgba(255,255,255,0.05)", color: "#64748b" }}>
                          {timeAgo(scan.scanned_at)}
                        </span>
                      </div>
                    </div>

                    {/* Stats row */}
                    <div className="mt-4 flex items-center gap-5">
                      <span className="text-xs" style={{ color: "#475569" }}>
                        <span className="text-white font-semibold">{files}</span> files
                      </span>
                      <span className="text-xs" style={{ color: "#475569" }}>
                        <span className="text-blue-400 font-semibold">{chunks}</span> chunks indexed
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-md"
                            style={{ background: "rgba(139,92,246,0.1)", color: "#a78bfa" }}>
                        {lang}
                      </span>
                      <span className="ml-auto text-xs font-medium transition-all group-hover:text-blue-400"
                            style={{ color: "#334155" }}>
                        Load →
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* CTA */}
          <button
            onClick={() => navigate("/repository")}
            className="w-full py-3.5 rounded-xl text-sm font-semibold transition-all duration-200 hover:opacity-90 fade-up"
            style={{ background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", color: "#fff" }}>
            + Analyze New Repository
          </button>

        </div>

        <p className="text-center text-xs py-6 mt-auto" style={{ color: "#334155" }}>
          Powered by py · 2026
        </p>
      </main>
    </div>
  );
}

export default RecentScans;
