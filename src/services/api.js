import axios from "axios";

// ─────────────────────────────────────────────
// Axios instance
// ─────────────────────────────────────────────
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "Content-Type": "application/json" },
});

export default API;

// ─────────────────────────────────────────────
// Step 1 — kick off background analysis job
// Returns: { job_id, status, message }
// ─────────────────────────────────────────────
export async function startAnalysis(repoUrl) {
  const res = await API.post("/analyze", null, {
    params: { repo_url: repoUrl },
  });
  return res.data;
}

// ─────────────────────────────────────────────
// Step 2 — poll /status/:jobId until done
// Calls onProgress(status, percent) every tick.
// Returns the final result object when done.
// ─────────────────────────────────────────────
export function pollStatus(jobId, onProgress, intervalMs = 2000) {
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const res  = await API.get(`/status/${jobId}`);
        const data = res.data;

        onProgress(data.status, data.progress ?? 0);

        if (data.status === "done") {
          clearInterval(timer);
          resolve(data.result);
        }

        if (data.status === "error") {
          clearInterval(timer);
          reject(new Error(data.error || "Analysis failed."));
        }

        if (data.status === "cancelled") {
          clearInterval(timer);
          reject(new Error("Cancelled by user."));
        }
      } catch (err) {
        clearInterval(timer);
        reject(err);
      }
    }, intervalMs);
  });
}

// ─────────────────────────────────────────────
// Cancel a running job
// ─────────────────────────────────────────────
export async function cancelAnalysis(jobId) {
  const res = await API.post(`/cancel/${jobId}`);
  return res.data;
}

// ─────────────────────────────────────────────
// Ask AI — scoped to a specific repo
// ─────────────────────────────────────────────
export async function askAI(question, repoUrl) {
  const res = await API.post("/ask", null, {
    params: { question, repo_url: repoUrl },
  });
  return res.data;
}