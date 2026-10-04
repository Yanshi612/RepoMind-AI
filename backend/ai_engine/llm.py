import os
import time
import warnings

# Suppress FutureWarning from any stale google.generativeai usage
warnings.filterwarnings("ignore", category=FutureWarning)

from dotenv import load_dotenv

load_dotenv()

# ── Use new google.genai SDK (replaces deprecated google.generativeai) ──
try:
    from google import genai
    from google.genai import types as genai_types
    _SDK = "new"
except ImportError:
    # Fallback to old SDK if new one not installed yet
    import google.generativeai as genai_old
    _SDK = "old"


def explain_code(question: str, code_context: str) -> str:
    """
    Calls Gemini to answer a question about repository code.
    Automatically uses the new google.genai SDK or falls back to
    the legacy google.generativeai SDK.
    """

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "" or "AQAb8RN6" in api_key:
        return (
            "⚠️ Missing or invalid GEMINI_API_KEY. "
            "Please add a valid key from Google AI Studio to backend/.env"
        )

    prompt = f"""You are an expert software engineer analyzing a GitHub repository.

Repository Code Context:
{code_context}

User Question:
{question}

Answer clearly and in detail. Mention file names where relevant."""

    # ── New SDK (google-genai) ────────────────────────────────────────────
    if _SDK == "new":
        candidate_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        client = genai.Client(api_key=api_key)
        last_error = None

        for model_name in candidate_models:
            for attempt in range(4):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    return response.text
                except Exception as e:
                    err_str = str(e).lower()
                    if any(k in err_str for k in ["429", "resource_exhausted", "quota", "rate limit", "too many requests"]):
                        wait = 5 * (2 ** attempt)
                        print(f"[llm] 429 Rate limit on '{model_name}'. Waiting {wait}s...")
                        time.sleep(wait)
                        last_error = e
                    else:
                        print(f"[llm] model '{model_name}' failed: {e}")
                        last_error = e
                        break

        return f"Gemini API rate limit exceeded. Please wait a minute and try again. ({last_error})"

    # ── Legacy SDK fallback (google-generativeai) ─────────────────────────
    else:
        candidate_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-pro",
        ]
        genai_old.configure(api_key=api_key)
        last_error = None

        for model_name in candidate_models:
            try:
                model    = genai_old.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"[llm] legacy model '{model_name}' failed: {e}")
                last_error = e

        return f"Gemini API error: {last_error}"