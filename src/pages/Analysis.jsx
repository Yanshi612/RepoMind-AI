import { useState, useEffect, useRef } from "react";
import Navbar from "../components/Navbar";
import { askAI } from "../services/api";

function Footer() {
  return (
    <p className="text-center text-xs py-6 mt-auto" style={{ color: "#334155" }}>
      Powered by RepoMind AI · Built with ♥ · 2025
    </p>
  );
}

function Analysis() {
  const [analysis, setAnalysis] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    const saved = localStorage.getItem("repositoryAnalysis");
    if (saved) { try { setAnalysis(JSON.parse(saved)); } catch {} }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleAsk = async () => {
    const q = question.trim();
    if (!q) return setError("Please type a question.");
    const repoUrl = analysis?.repo_url;
    if (!repoUrl) return setError("No repository found. Please analyze one first.");

    setError("");
    setMessages(prev => [...prev, { role: "user", text: q }]);
    setQuestion("");
    setLoading(true);

    try {
      const data = await askAI(q, repoUrl);
      setMessages(prev => [...prev, { role: "ai", text: data.answer }]);
    } catch (err) {
      const msg = err.response?.data?.detail || "Something went wrong.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#07080f", color: "#f1f5f9" }}>
      <Navbar />

      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10 flex flex-col gap-7">

        {/* Heading */}
        <div className="fade-up">
          <h1 className="text-3xl font-bold tracking-tight">AI Analysis</h1>
          <p className="mt-1.5 text-sm" style={{ color: "#64748b" }}>
            Ask questions about your indexed repository's code, structure, and logic.
          </p>
        </div>

        {/* No repo */}
        {!analysis && (
          <div className="rounded-2xl p-12 text-center fade-up"
               style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}>
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
                 style={{ background: "rgba(59,130,246,0.1)", color: "#3b82f6" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">No Repository Indexed</h2>
            <p className="text-sm mb-6" style={{ color: "#64748b" }}>
              Analyze a GitHub repository first to enable AI Q&A.
            </p>
            <button
              onClick={() => window.location.href = "/repository"}
              className="px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:opacity-90"
              style={{ background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", color: "#fff" }}>
              Analyze a Repository
            </button>
          </div>
        )}

        {analysis && (
          <>
            {/* Stats row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 fade-up">
              {[
                { label: "Total Files", value: analysis.stats?.total_files,      color: "#3b82f6" },
                { label: "Python",      value: analysis.stats?.python_files,      color: "#f59e0b" },
                { label: "JavaScript",  value: analysis.stats?.javascript_files,  color: "#eab308" },
                { label: "Chunks",      value: analysis.vector_db?.chunks_stored ?? analysis.vector_db?.chunks ?? 0, color: "#8b5cf6" },
              ].map(({ label, value, color }) => (
                <div key={label} className="rounded-2xl p-5 transition-all duration-200 hover:scale-105"
                     style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)" }}>
                  <p className="text-xs mb-1" style={{ color: "#64748b" }}>{label}</p>
                  <p className="text-2xl font-bold" style={{ color }}>{value ?? 0}</p>
                </div>
              ))}
            </div>

            {/* Repo badge */}
            <div className="flex items-center gap-2 fade-up">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-mono truncate" style={{ color: "#475569" }}>
                {analysis.repo_url}
              </span>
            </div>

            {/* Chat window */}
            <div className="flex-1 rounded-2xl flex flex-col overflow-hidden fade-up"
                 style={{ background: "#111422", border: "1px solid rgba(255,255,255,0.07)", minHeight: "420px" }}>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5" style={{ maxHeight: "460px" }}>
                {messages.length === 0 && !loading && (
                  <div className="flex flex-col items-center justify-center h-full gap-3"
                       style={{ color: "#334155" }}>
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    <p className="text-sm">Ask anything about the repository…</p>
                  </div>
                )}

                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                    <div className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                         style={{ background: msg.role === "user" ? "#3b82f6" : "#7c3aed" }}>
                      {msg.role === "user" ? "U" : "AI"}
                    </div>
                    <div className="rounded-2xl px-4 py-3 text-sm leading-7 whitespace-pre-wrap max-w-[78%]"
                         style={msg.role === "user"
                           ? { background: "rgba(59,130,246,0.12)", border: "1px solid rgba(59,130,246,0.2)", color: "#bfdbfe", borderRadius: "16px 4px 16px 16px" }
                           : { background: "#1e293b", border: "1px solid rgba(255,255,255,0.07)", color: "#e2e8f0", borderRadius: "4px 16px 16px 16px" }
                         }>
                      {msg.text}
                    </div>
                  </div>
                ))}

                {/* Typing indicator */}
                {loading && (
                  <div className="flex gap-3">
                    <div className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                         style={{ background: "#7c3aed" }}>AI</div>
                    <div className="px-4 py-3 rounded-2xl flex items-center gap-1.5"
                         style={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "4px 16px 16px 16px" }}>
                      {[0, 150, 300].map(d => (
                        <span key={d} className="w-2 h-2 rounded-full animate-bounce"
                              style={{ background: "#8b5cf6", animationDelay: `${d}ms` }} />
                      ))}
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Divider */}
              <div style={{ height: "1px", background: "rgba(255,255,255,0.05)" }} />

              {/* Input */}
              <div className="p-4 flex gap-3 items-end">
                <textarea
                  id="question-input"
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey && !loading) { e.preventDefault(); handleAsk(); } }}
                  placeholder="Ask about the code… (Enter to send)"
                  rows={2}
                  disabled={loading}
                  className="flex-1 px-4 py-3 text-sm rounded-xl resize-none input-glow transition-all"
                  style={{ background: "#0d0f1a", border: "1px solid rgba(255,255,255,0.1)", color: "#f1f5f9", outline: "none", opacity: loading ? 0.6 : 1 }}
                />
                <button
                  id="ask-btn"
                  onClick={handleAsk}
                  disabled={loading || !question.trim()}
                  className="px-5 py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:opacity-90 shrink-0"
                  style={{ background: loading || !question.trim() ? "#1e293b" : "linear-gradient(135deg,#8b5cf6,#3b82f6)", color: loading || !question.trim() ? "#475569" : "#fff", cursor: loading ? "not-allowed" : "pointer" }}>
                  {loading ? "…" : "Ask"}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-xl px-4 py-3 text-sm"
                   style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171" }}>
                {error}
              </div>
            )}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default Analysis;
