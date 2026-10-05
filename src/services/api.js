import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "https://repo-mind-ai-pdyq.vercel.app",
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
    let timer = null;

    const check = async () => {
      try {
        const res = await API.get(`/status/${jobId}`);
        const data = res.data;

        onProgress(data.status, data.progress ?? 0);

        if (data.status === "done") {
          if (timer) clearInterval(timer);
          resolve(data.result);
          return true;
        }

        if (data.status === "error") {
          if (timer) clearInterval(timer);
          reject(new Error(data.error || "Analysis failed."));
          return true;
        }

        if (data.status === "cancelled") {
          if (timer) clearInterval(timer);
          reject(new Error("Cancelled by user."));
          return true;
        }
      } catch (err) {
        if (timer) clearInterval(timer);
        const detail = err.response?.data?.detail || err.message || "Analysis failed.";
        reject(new Error(detail));
        return true;
      }
      return false;
    };

    check().then((finished) => {
      if (!finished) {
        timer = setInterval(check, intervalMs);
      }
    });
  });
}

export async function cancelAnalysis(jobId) {
  const res = await API.post(`/cancel/${jobId}`);
  return res.data;
}

export async function askAI(question, repoUrl) {
  const res = await API.post("/ask", null, {
    params: { question, repo_url: repoUrl },
  });
  return res.data;
}

