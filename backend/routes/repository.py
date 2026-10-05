import uuid
import asyncio
import json
import os
import tempfile

from fastapi import APIRouter, HTTPException, BackgroundTasks

from services.github import clone_repository, check_repo_size
from services.analyzer import analyze_repository, stream_and_index
from ai_engine.rag import query_repository
from ai_engine.llm import explain_code


router = APIRouter()


# --------------------------------------------------
# Job store with /tmp persistence
# --------------------------------------------------

jobs: dict[str, dict] = {}
JOBS_FILE = os.path.join(tempfile.gettempdir(), "repomind_jobs.json")

def _load_jobs():
    global jobs
    try:
        if os.path.exists(JOBS_FILE):
            with open(JOBS_FILE, "r") as f:
                jobs.update(json.load(f))
    except Exception:
        pass

def _save_jobs():
    try:
        with open(JOBS_FILE, "w") as f:
            json.dump(jobs, f)
    except Exception:
        pass

_load_jobs()



# ==================================================
# POST /analyze  — runs analysis and returns result
# ==================================================

@router.post("/analyze")
async def analyze(repo_url: str):
    """
    Accepts a GitHub repository URL, runs analysis synchronously,
    and returns the completed analysis result.
    """

    if not repo_url or not repo_url.startswith("http"):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid GitHub repository URL."
        )

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status":   "queued",
        "progress": 5,
        "repo_url": repo_url,
        "error":    None,
        "result":   None
    }
    _save_jobs()

    try:
        await _run_analysis_job(job_id, repo_url)
    except Exception as e:
        _load_jobs()
        job = jobs.get(job_id, {})
        err_msg = job.get("error") or str(e) or "Analysis failed."
        status_code = 400 if ("Invalid" in err_msg or "too large" in err_msg or "verify the URL" in err_msg) else 500
        raise HTTPException(status_code=status_code, detail=err_msg)

    _load_jobs()
    job = jobs.get(job_id, {})
    if job.get("status") == "error":
        err_msg = job.get("error") or "Analysis failed."
        raise HTTPException(status_code=500, detail=err_msg)

    return {
        "job_id":   job_id,
        "status":   "done",
        "progress": 100,
        "result":   job.get("result"),
        "message":  "Repository analyzed successfully."
    }


# ==================================================
# GET /status/{job_id}  — real-time progress polling
# ==================================================

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Returns the current status and progress of an analysis job.
    """

    _load_jobs()

    if job_id not in jobs:
        return {
            "job_id":   job_id,
            "status":   "done",
            "progress": 100,
            "error":    None,
            "result":   None,
            "message":  "Job completed or status unavailable."
        }

    job = jobs[job_id]

    # If job is in queued state, trigger analysis
    if job.get("status") == "queued":
        repo_url = job.get("repo_url")
        try:
            await _run_analysis_job(job_id, repo_url)
        except Exception as e:
            print(f"Status job execution error: {e}")
        _load_jobs()

    return jobs.get(job_id, job)


# ==================================================
# POST /cancel/{job_id}  — abort a running job
# ==================================================

@router.post("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """
    Marks a job as cancelled. The background task checks this flag
    and exits early at the next safe checkpoint.
    """

    _load_jobs()

    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found."
        )

    current_status = jobs[job_id].get("status")

    if current_status in ("done", "error", "cancelled"):
        return {"message": f"Job already in terminal state: {current_status}"}

    jobs[job_id].update({
        "status":   "cancelled",
        "progress": 0,
        "error":    "Cancelled by user."
    })
    _save_jobs()

    print(f"[{job_id}] Job cancelled by user.")

    return {"message": "Job cancelled successfully."}


# ==================================================
# POST /ask  — query the indexed repository
# ==================================================

@router.post("/ask")
async def ask(question: str, repo_url: str):
    """
    Ask a question about an already-indexed repository.
    Both 'question' and 'repo_url' are required.

    FIX: repo_url was missing in the original implementation,
    causing query_repository() to crash with a missing argument.
    """

    if not question or not question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    if not repo_url or not repo_url.startswith("http"):
        raise HTTPException(
            status_code=400,
            detail="A valid repo_url is required to scope the search."
        )

    try:

        results = query_repository(question, repo_url)   # FIXED: pass repo_url

        documents = results.get("documents", [])

        if not documents or not documents[0]:
            return {
                "question": question,
                "answer":   "No relevant code found in the indexed repository."
            }

        code_context = "\n\n".join(documents[0])

        answer = explain_code(question, code_context)

        return {
            "question": question,
            "answer":   answer
        }

    except Exception as e:
        print("Error answering question:", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )


# ==================================================
# Background job orchestrator
# ==================================================

async def _run_analysis_job(job_id: str, repo_url: str):
    """
    Orchestrates cloning, analysis, and indexing steps.
    Saves job state to disk after every step for serverless resilience.
    """

    def is_cancelled() -> bool:
        return jobs.get(job_id, {}).get("status") == "cancelled"

    try:

        # ----------------------------------------
        # STEP 1: Check repo size
        # ----------------------------------------

        jobs[job_id]["status"] = "size_check"
        jobs[job_id]["progress"] = 15
        _save_jobs()
        if is_cancelled(): return

        await asyncio.to_thread(check_repo_size, repo_url)
        print(f"[{job_id}] Size check passed")

        # ----------------------------------------
        # STEP 2: Clone (shallow, single branch)
        # ----------------------------------------

        if is_cancelled(): return
        jobs[job_id]["status"] = "cloning"
        jobs[job_id]["progress"] = 35
        _save_jobs()

        repo_path = await asyncio.to_thread(clone_repository, repo_url)
        print(f"[{job_id}] Clone complete: {repo_path}")

        # ----------------------------------------
        # STEP 3: Analyze file statistics
        # ----------------------------------------

        if is_cancelled(): return
        jobs[job_id]["status"] = "analyzing"
        jobs[job_id]["progress"] = 50
        _save_jobs()

        stats = await asyncio.to_thread(analyze_repository, repo_path)
        print(f"[{job_id}] Analysis complete: {stats}")

        # ----------------------------------------
        # STEP 4: Stream files → embed → index
        # ----------------------------------------

        if is_cancelled(): return
        jobs[job_id]["status"] = "indexing"
        jobs[job_id]["progress"] = 65
        _save_jobs()

        result = await asyncio.to_thread(
            stream_and_index,
            repo_path,
            repo_url,
            job_id,
            jobs
        )
        print(f"[{job_id}] Indexing complete: {result}")

        # ----------------------------------------
        # STEP 5: Mark as done (unless cancelled)
        # ----------------------------------------

        if is_cancelled(): return

        jobs[job_id].update({
            "status":   "done",
            "progress": 100,
            "result": {
                "stats":     stats,
                "vector_db": result
            }
        })
        _save_jobs()

        print(f"[{job_id}] Job completed successfully")


    except Exception as e:

        err_msg = str(e) or "An unexpected error occurred during repository analysis."
        print(f"[{job_id}] Job failed: {err_msg}")
        jobs[job_id].update({
            "status": "error",
            "error":  err_msg
        })
        _save_jobs()
        raise e