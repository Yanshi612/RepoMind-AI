import { useState, useRef } from "react";
import Sidebar from "../components/Sidebar";
import { startAnalysis, pollStatus } from "../services/api";
import API from "../services/api";

/* ─── Step metadata ─────────────────────────────────────────── */
const STEPS = [
  { key: "size_check", label: "Size Check"  },
  { key: "cloning",    label: "Cloning"     },
  { key: "analyzing",  label: "Analyzing"   },
  { key: "indexing",   label: "Indexing"    },
  { key: "done",       label: "Complete"    },
];

const STATUS_LABEL = {
  queued:     "Waiting to start…",
  size_check: "Checking repository size…",
  cloning:    "Cloning repository (shallow)…",
  analyzing:  "Scanning files & structure…",
  indexing:   "Building AI knowledge base…",
  done:       "Analysis complete!",
  cancelled:  "Cancelled by user.",
  error:      "Something went wrong.",
};

function stepIndex(status) {
  const i = STEPS.findIndex(s => s.key === status);
  return i === -1 ? (status === "done" ? STEPS.length : 0) : i;
}

/* ─── Footer ────────────────────────────────────────────────── */
function Footer() {
  return (
    <p className="text-center text-xs py-6 mt-auto" style={{ color: "#334155" }}>
      Powered by RepoMind AI · Built with ♥ · 2025
    </p>
  );
}

/* ─── Main Component ────────────────────────────────────────── */
function Repository() {
  const [repoUrl,   setRepoUrl]   = useState("");
  const [jobId,     setJobId]     = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [progress,  setProgress]  = useState(0);
  const [result,    setResult]    = useState(null);
  const [error,     setError]     = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  const pollRef = useRef(null);   // holds the setInterval id from pollStatus

  /* ── Start analysis ─────────────────────────────────────── */
  const handleAnalyze = async () => {
    const url = repoUrl.trim();
    if (!url)                    return setError("Please enter a GitHub repository URL.");
    if (!url.startsWith("http")) return setError("URL must start with https://");

    setError(null);
    setResult(null);
    setProgress(5);
    setJobStatus("size_check");
    setIsRunning(true);
    setJobId(null);

    // Simulated smooth progress update while waiting for backend response
    const fakeProgressTimer = setInterval(() => {
      setProgress((prev) => {
        if (prev < 20) {
          setJobStatus("size_check");
          return prev + 5;
        } else if (prev < 45) {
          setJobStatus("cloning");
          return prev + 4;
        } else if (prev < 65) {
          setJobStatus("analyzing");
          return prev + 3;
        } else if (prev < 90) {
          setJobStatus("indexing");
          return prev + 2;
        }
        return prev;
      });
    }, 400);

    try {
      const responseData = await startAnalysis(url);
      clearInterval(fakeProgressTimer);

      if (responseData?.job_id) {
        setJobId(responseData.job_id);
      }

      let finalResult = responseData?.result;

      // If backend returned queued instead of done, fallback to polling
      if (responseData?.status !== "done" && responseData?.job_id) {
        finalResult = await pollStatus(responseData.job_id, (status, pct) => {
          setJobStatus(status);
          setProgress(pct);
          if (status === "cancelled") {
            setIsRunning(false);
          }
        });
      }

      if (!finalResult) {
        throw new Error("No analysis data returned from backend.");
      }

      const payload = {
        ...finalResult,
        repo_url: url,
        scanned_at: new Date().toISOString(),
      };

      localStorage.setItem("repositoryAnalysis", JSON.stringify(payload));

      try {
        const prev = JSON.parse(localStorage.getItem("recentScans") || "[]");
        const deduped = prev.filter((s) => s.repo_url !== url);
        deduped.push(payload);
        localStorage.setItem("recentScans", JSON.stringify(deduped.slice(-20)));
      } catch {
        /* ignore */
      }

      setResult(payload);
      setJobStatus("done");
      setProgress(100);
    } catch (err) {
      clearInterval(fakeProgressTimer);
      const errMsg =
        err.response?.data?.detail || err.message || "Analysis failed.";
      setError(errMsg);
      setJobStatus("error");
    } finally {
      setIsRunning(false);
    }
  };

  /* ── Cancel analysis ────────────────────────────────────── */
  const handleCancel = async () => {
    if (!jobId) { setIsRunning(false); setJobStatus(null); return; }
    try {
      await API.post(`/cancel/${jobId}`);
    } catch (_) { /* best-effort */ }
    setJobStatus("cancelled");
    setIsRunning(false);
    setError("Analysis was cancelled.");
  };

  /* ── Reset ──────────────────────────────────────────────── */
  const handleReset = () => {
    setRepoUrl(""); setJobId(null); setJobStatus(null);
    setProgress(0); setResult(null); setError(null); setIsRunning(false);
  };

  const curStepIdx = stepIndex(jobStatus);
  const showTracker = isRunning || ["done","cancelled","error"].includes(jobStatus);

  return (
    <div className="flex min-h-screen" style={{ background: "#07080f", color: "#f1f5f9" }}>
      <Sidebar />

      <main className="flex-1 flex flex-col p-8 md:p-12 overflow-auto">
        <div className="max-w-2xl w-full mx-auto flex-1 flex flex-col gap-7">

          {/* ── Heading ─────────────────────────────────── */}
          <div className="fade-up">
            <h1 className="text-3xl font-bold tracking-tight">Analyze Repository</h1>
            <p className="mt-1.5 text-sm" style={{ color: "#64748b" }}>
              Connect a GitHub repository to index its code and unlock AI questions.
            </p>
          </div>

          {/* ── Input card ──────────────────────────────── */}
          <div className="rounded-2xl p-7 fade-up"
               style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}>

            <label className="block text-xs font-semibold uppercase tracking-widest mb-2"
                   style={{ color: "#64748b" }}>
              GitHub Repository URL
            </label>

            <input
              id="repo-url-input"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !isRunning && handleAnalyze()}
              placeholder="https://github.com/user/repository"
              disabled={isRunning}
              className="input-glow w-full px-4 py-3 rounded-xl text-sm transition-all"
              style={{
                background: "#0d0f1a",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#f1f5f9",
                outline: "none",
                opacity: isRunning ? 0.5 : 1,
              }}
            />

            <div className="flex gap-3 mt-5">
              {/* Analyze button */}
              <button
                id="analyze-btn"
                onClick={handleAnalyze}
                disabled={isRunning}
                className="flex-1 py-3 rounded-xl text-sm font-semibold transition-all duration-200"
                style={{
                  background: isRunning
                    ? "#1e293b"
                    : "linear-gradient(135deg,#3b82f6,#8b5cf6)",
                  color: isRunning ? "#475569" : "#fff",
                  cursor: isRunning ? "not-allowed" : "pointer",
                }}
              >
                {isRunning ? "Analyzing…" : "Analyze Repository"}
              </button>

              {/* Cancel button — only during active run */}
              {isRunning && (
                <button
                  id="cancel-btn"
                  onClick={handleCancel}
                  className="px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:opacity-80"
                  style={{
                    background: "rgba(239,68,68,0.12)",
                    border: "1px solid rgba(239,68,68,0.35)",
                    color: "#f87171",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              )}

              {/* Reset button — after completion */}
              {!isRunning && jobStatus && (
                <button
                  onClick={handleReset}
                  className="px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:opacity-80"
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "#94a3b8",
                    cursor: "pointer",
                  }}
                >
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* ── Progress tracker ────────────────────────── */}
          {showTracker && (
            <div className="rounded-2xl p-7 fade-up"
                 style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}>

              {/* Status text */}
              <div className="flex items-center justify-between mb-5">
                <div>
                  <p className="text-sm font-semibold" style={{
                    color: jobStatus === "done"      ? "#4ade80"
                         : jobStatus === "error"     ? "#f87171"
                         : jobStatus === "cancelled" ? "#f59e0b"
                         : "#60a5fa"
                  }}>
                    {STATUS_LABEL[jobStatus] ?? "Processing…"}
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: "#475569" }}>
                    {progress}% complete
                  </p>
                </div>
                {isRunning && (
                  <div className="w-2 h-2 rounded-full relative" style={{ color: "#3b82f6" }}>
                    <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
                  </div>
                )}
              </div>

              {/* Progress bar */}
              <div className="w-full h-1.5 rounded-full mb-7 overflow-hidden"
                   style={{ background: "#1e293b" }}>
                <div
                  id="progress-bar"
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${progress}%`,
                    background: jobStatus === "error"     ? "#ef4444"
                               : jobStatus === "cancelled" ? "#f59e0b"
                               : undefined,
                  }}
                >
                  {!["error","cancelled"].includes(jobStatus) && (
                    <div className="progress-shimmer w-full h-full rounded-full" />
                  )}
                </div>
              </div>

              {/* Step pipeline */}
              <div className="flex items-center">
                {STEPS.map((step, i) => {
                  const done   = i < curStepIdx || jobStatus === "done";
                  const active = i === curStepIdx && !["done","error","cancelled"].includes(jobStatus);
                  const last   = i === STEPS.length - 1;

                  return (
                    <div key={step.key} className="flex items-center flex-1 min-w-0">
                      <div className="flex flex-col items-center shrink-0 gap-1">
                        {/* Circle */}
                        <div
                          className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300"
                          style={{
                            background: done   ? "#3b82f6"
                                       : active ? "#8b5cf6"
                                       : "#1e293b",
                            color:  done || active ? "#fff" : "#475569",
                            boxShadow: active ? "0 0 14px rgba(139,92,246,0.5)" : "none",
                          }}
                        >
                          {done ? "✓" : i + 1}
                        </div>
                        {/* Label */}
                        <span className="text-center leading-tight"
                              style={{
                                fontSize: "0.58rem",
                                color: done ? "#60a5fa" : active ? "#a78bfa" : "#334155",
                              }}>
                          {step.label}
                        </span>
                      </div>
                      {!last && (
                        <div className="h-px flex-1 mx-1 transition-all duration-500"
                             style={{ background: i < curStepIdx ? "#3b82f6" : "#1e293b" }} />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Error ───────────────────────────────────── */}
          {error && (
            <div className="rounded-xl px-5 py-4 text-sm fade-up"
                 style={{ background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.25)", color:"#f87171" }}>
              {error}
            </div>
          )}

          {/* ── Success result ──────────────────────────── */}
          {result && !error && (
            <div className="space-y-5 fade-up">

              {/* Banner */}
              <div className="rounded-2xl px-6 py-5"
                   style={{ background:"rgba(74,222,128,0.07)", border:"1px solid rgba(74,222,128,0.2)" }}>
                <p className="font-semibold text-green-400">Repository indexed successfully ✓</p>
                <p className="text-xs mt-1" style={{ color:"#64748b" }}>
                  The codebase is now searchable. Head to Analysis to ask AI questions.
                </p>
              </div>

              {/* Stats */}
              {result.stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label:"Total Files",  value: result.stats.total_files,       icon:"📁" },
                    { label:"Python",       value: result.stats.python_files,       icon:"🐍" },
                    { label:"JavaScript",   value: result.stats.javascript_files,   icon:"🟨" },
                    { label:"TypeScript",   value: result.stats.typescript_files,   icon:"🔷" },
                  ].map(({ label, value, icon }) => (
                    <div key={label} className="rounded-2xl p-5"
                         style={{ background:"#111422", border:"1px solid rgba(255,255,255,0.07)" }}>
                      <p className="text-base mb-1">{icon}</p>
                      <p className="text-xs" style={{ color:"#64748b" }}>{label}</p>
                      <p className="text-2xl font-bold mt-1">{value ?? 0}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Vector DB */}
              {result.vector_db && (
                <div className="rounded-2xl px-6 py-5"
                     style={{ background:"#111422", border:"1px solid rgba(255,255,255,0.07)" }}>
                  <p className="text-sm font-semibold mb-3">AI Knowledge Base</p>
                  <div className="flex gap-6">
                    <div>
                      <p className="text-2xl font-bold text-blue-400">
                        {result.vector_db.chunks_stored ?? result.vector_db.chunks ?? 0}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color:"#64748b" }}>chunks indexed</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-400">
                        {result.vector_db.files_scanned ?? "—"}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color:"#64748b" }}>files scanned</p>
                    </div>
                  </div>
                </div>
              )}

              {/* CTA */}
              <button
                id="go-to-analysis-btn"
                onClick={() => window.location.href = "/analysis"}
                className="w-full py-4 rounded-xl font-semibold text-sm transition-all duration-200 hover:opacity-90"
                style={{ background:"linear-gradient(135deg,#8b5cf6,#3b82f6)", color:"#fff" }}
              >
                Ask AI About This Repository →
              </button>
            </div>
          )}

        </div>

        <Footer />
      </main>
    </div>
  );
}

export default Repository;
