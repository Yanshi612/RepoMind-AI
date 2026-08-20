import os
import shutil
import hashlib

# Limit BLAS threads — prevents OpenBLAS memory allocation errors
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS",      "1")
os.environ.setdefault("MKL_NUM_THREADS",      "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import chromadb

from sentence_transformers import SentenceTransformer

from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# Persistent ChromaDB client  —  with auto-recovery
# ============================================================

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")


def _make_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


def _make_collection(c):
    try:
        return c.get_collection(name="repo_code")
    except Exception:
        return c.create_collection(name="repo_code")


def _init_chroma():
    """
    Initialise ChromaDB. If the HNSW index is corrupted (common after
    a hard crash), wipe the data directory and start fresh automatically.
    """
    global client, collection
    try:
        client     = _make_client()
        collection = _make_collection(client)
        # Probe — triggers HNSW load so corruption surfaces here, not mid-request
        collection.count()
    except Exception as e:
        if "hnsw" in str(e).lower() or "segment" in str(e).lower() or "compaction" in str(e).lower():
            print(f"[rag] ChromaDB index corrupted ({e}). Wiping and reinitialising…")
            try:
                shutil.rmtree(CHROMA_PATH, ignore_errors=True)
            except Exception:
                pass
            client     = _make_client()
            collection = _make_collection(client)
            print("[rag] ChromaDB reinitialised successfully.")
        else:
            raise


client     = None
collection = None
_init_chroma()


# ============================================================
# Lazy-load embedding model (Fix 6)
# Avoids loading ~800 MB model at import time.
# Model initialises on the first actual request.
# ============================================================

_embedding_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Returns the singleton SentenceTransformer model.
    Loads it on first call only — not at module import.
    """

    global _embedding_model

    if _embedding_model is None:
        print("RAG: Loading embedding model (first use)...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("RAG: Embedding model ready.")

    return _embedding_model


# ============================================================
# Repository ID helper
# ============================================================

def get_repo_id(repo_url: str) -> str:
    return hashlib.md5(repo_url.rstrip("/").encode()).hexdigest()[:12]


# ============================================================
# Per-file streaming index (Fix 7)
# Called once per file from stream_and_index() in analyzer.py.
# Never accumulates all documents in RAM simultaneously.
# ============================================================

def index_chunks_stream(
    chunks:    list[str],
    file_name: str,
    repo_url:  str
) -> None:
    """
    Embeds and upserts text chunks for a single file into ChromaDB.

    Uses upsert() instead of add() to safely re-index repos without
    duplicate chunk errors on repeated analysis of the same repository.
    """

    repo_id = get_repo_id(repo_url)
    model   = get_embedding_model()

    EMBEDDING_BATCH_SIZE = 64

    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):

        batch = chunks[start : start + EMBEDDING_BATCH_SIZE]

        # Encode this micro-batch
        vectors = model.encode(
            batch,
            batch_size=32,
            show_progress_bar=False
        )

        ids = [
            f"{repo_id}_{hashlib.md5(f'{file_name}_{start + i}'.encode()).hexdigest()[:10]}"
            for i in range(len(batch))
        ]

        embeddings = [v.tolist() for v in vectors]

        metadatas = [
            {"repo_id": repo_id, "file": file_name}
            for _ in batch
        ]

        # FIX: upsert prevents duplicate-ID errors on re-analysis
        collection.upsert(
            ids=ids,
            documents=batch,
            embeddings=embeddings,
            metadatas=metadatas
        )


# ============================================================
# Store Repository Code (legacy batch path — kept for reference)
# New code should call index_chunks_stream() per file instead.
# ============================================================

def store_code_in_vector_db(
    documents: list[dict],
    repo_url:  str
) -> dict:
    """
    Batch-indexes a list of {file_name, content} documents.
    Kept for backward compatibility with extract_code_files().
    """

    repo_id = get_repo_id(repo_url)

    print(f"Repository ID: {repo_id}")

    # --------------------------------------------------------
    # Delete old vectors for this repo before re-indexing
    # --------------------------------------------------------

    try:
        collection.delete(where={"repo_id": repo_id})
        print("Old repository vectors removed.")
    except Exception as e:
        print(f"No old vectors to remove: {e}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    total_chunks = 0

    for doc in documents:
        chunks = splitter.split_text(doc["content"])
        if chunks:
            index_chunks_stream(chunks, doc["file_name"], repo_url)
            total_chunks += len(chunks)

    if total_chunks == 0:
        return {"message": "No code files found.", "chunks": 0, "repo_id": repo_id}

    print("Repository stored successfully.")

    return {
        "message":  "Code stored successfully",
        "chunks":   total_chunks,
        "repo_id":  repo_id
    }


# ============================================================
# Query Repository
# ============================================================

def query_repository(question: str, repo_url: str) -> dict:
    """
    Searches ChromaDB for chunks relevant to the question,
    scoped strictly to the specified repository (via repo_id).
    """

    repo_id = get_repo_id(repo_url)
    model   = get_embedding_model()

    print(f"RAG: Searching repository {repo_id}")
    print(f"RAG: Question: {question}")

    # --------------------------------------------------------
    # Embed the question
    # --------------------------------------------------------

    question_embedding = model.encode(question).tolist()

    # --------------------------------------------------------
    # Search ONLY within this repository's chunks
    # --------------------------------------------------------

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5,
        where={"repo_id": repo_id}
    )

    print(
        "RAG: Relevant chunks found:",
        len(results.get("documents", [[]])[0])
    )

    return results