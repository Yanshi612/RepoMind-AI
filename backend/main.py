import os

# ── Prevent OpenBLAS / OMP memory allocation failures ──────────────
# Must be set before numpy/torch/sentence-transformers are imported.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS",      "1")
os.environ.setdefault("MKL_NUM_THREADS",      "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS",  "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.repository import router



# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="RepoMind AI",
    description="AI-powered GitHub Repository Analysis System",
    version="1.0.0"
)


# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],
)


# --------------------------------------------------
# Repository Routes
# --------------------------------------------------

app.include_router(router)


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "status": "success",
        "message": "RepoMind AI Backend is running"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }