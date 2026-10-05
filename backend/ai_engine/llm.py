import os
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types as genai_types
    _SDK = "new"
except ImportError:
    import google.generativeai as genai_old
    _SDK = "old"


def explain_code(question: str, code_context: str) -> str:
    """
    Calls Gemini to answer a question about repository code.
    Tries multiple candidate models with instant fallback for 503 / 429 capacity errors.
    """

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "" or "AQAb8RN6" in api_key:
        return (
            "⚠️ Missing or invalid GEMINI_API_KEY in environment variables.\n"
            "Please ensure `GEMINI_API_KEY` is configured in your Vercel project environment variables."
        )

    prompt = f"""You are an expert software engineer analyzing a GitHub repository.

Repository Code Context:
{code_context}

User Question:
{question}

Answer clearly and in detail. Mention file names and code lines where relevant."""

    candidate_models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]

    last_error = None

    # ── New SDK (google-genai) ────────────────────────────────────────────
    if _SDK == "new":
        client = genai.Client(api_key=api_key)

        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[llm] Model '{model_name}' failed or busy: {e}")
                last_error = e
                continue

    # ── Legacy SDK fallback (google-generativeai) ─────────────────────────
    else:
        genai_old.configure(api_key=api_key)

        for model_name in candidate_models:
            try:
                model    = genai_old.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[llm] Legacy model '{model_name}' failed: {e}")
                last_error = e
                continue

    # ── Code Context Fallback if all models rate-limited / unavailable ────
    if code_context and code_context.strip():
        return (
            f"### 🔍 Codebase Search Results for: \"{question}\"\n\n"
            f"Here are the relevant code snippets retrieved from your repository:\n\n"
            f"{code_context}\n\n"
            "*(Note: Gemini LLM text generation model was temporarily busy, so the matching code snippets from your repository are displayed above.)*"
        )

    return f"Gemini API model temporarily unavailable: {last_error}. Please try asking again in a few seconds."