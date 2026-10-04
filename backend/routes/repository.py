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
# POST /analyze  — returns instantly with a job_id
# ==================================================

@router.post("/analyze")
async def analyze(repo_url: str, background_tasks: BackgroundTasks):
    """
    Accepts a GitHub repository URL and immediately returns a job_id.
    The actual cloning, analysis, and indexing runs in the background.
    Poll GET /status/{job_id} to track progress.
    """

    # --------------------------------------------------
    # Validate URL
    # --------------------------------------------------

    if not repo_url or not repo_url.startswith("http"):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid GitHub repository URL."
        )

    # --------------------------------------------------
    # Create job entry
    # --------------------------------------------------

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status":   "queued",
        "progress": 0,
        "repo_url": repo_url,
        "error":    None,
        "result":   None
    }
    _save_jobs()

    # --------------------------------------------------
    # Schedule background work — does NOT block
    # --------------------------------------------------

    background_tasks.add_task(_run_analysis_job, job_id, repo_url)

    return {
        "job_id":  job_id,
        "status":  "queued",
        "message": "Repository analysis started. Poll /status/{job_id} for progress."
    }


# ==================================================
# GET /status/{job_id}  — real-time progress polling
# ==================================================

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Returns the current status and progress of an analysis job.

    Possible statuses:
      queued      → job is waiting to start
      size_check  → checking repo size via GitHub API
      cloning     → git clone --depth 1 in progress
      analyzing   → counting files and building stats
      indexing    → embedding + storing in ChromaDB (progress 0-100)
      done        → completed successfully
      cancelled   → user aborted the job
      error       → failed (check 'error' field)
    """

    _load_jobs()

    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found."
        )

    return jobs[job_id]


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
    Orchestrates all heavy work off the HTTP request thread.
    asyncio.to_thread() runs each blocking call on a thread pool,
    keeping the FastAPI event loop free for other requests.
    Checks for cancellation between every step.
    """

    def is_cancelled() -> bool:
        return jobs.get(job_id, {}).get("status") == "cancelled"

    try:

        # ----------------------------------------
        # STEP 1: Check repo size
        # ----------------------------------------

        jobs[job_id]["status"] = "size_check"
        if is_cancelled(): return

        await asyncio.to_thread(check_repo_size, repo_url)
        print(f"[{job_id}] Size check passed")

        # ----------------------------------------
        # STEP 2: Clone (shallow, single branch)
        # ----------------------------------------

        if is_cancelled(): return
        jobs[job_id]["status"] = "cloning"

        repo_path = await asyncio.to_thread(clone_repository, repo_url)
        print(f"[{job_id}] Clone complete: {repo_path}")

        # ----------------------------------------
        # STEP 3: Analyze file statistics
        # ----------------------------------------

        if is_cancelled(): return
        jobs[job_id]["status"] = "analyzing"

        stats = await asyncio.to_thread(analyze_repository, repo_path)
        print(f"[{job_id}] Analysis complete: {stats}")

        # ----------------------------------------
        # STEP 4: Stream files → embed → index
        # ----------------------------------------

        if is_cancelled(): return
        jobs[job_id]["status"] = "indexing"

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

        if not is_cancelled():
            print(f"[{job_id}] Job failed: {e}")
            jobs[job_id].update({
                "status": "error",
                "error":  str(e)
            })
            _save_jobs()