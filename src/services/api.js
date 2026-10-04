import axios from "axios";

const API = axios.create({
  baseURL: "https://repo-mind-ai-pdyq-5gefvdjnb-yanshi612s-projects.vercel.app",
});

export default API;

export async function startAnalysis(repoUrl) {
  const res = await API.post("/analyze", null, {
    params: { repo_url: repoUrl },
  });
  return res.data;
}

export function pollStatus(jobId, onProgress, intervalMs = 2000) {
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const res = await API.get(/status/);
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

export async function cancelAnalysis(jobId) {
  const res = await API.post(/cancel/);
  return res.data;
}

export async function askAI(question, repoUrl) {
  const res = await API.post("/ask", null, {
    params: { question, repo_url: repoUrl },
  });
  return res.data;
}
