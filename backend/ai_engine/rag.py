import os
import hashlib
import math
import time
from array import array

from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# In-memory repository index for the current server instance.
# This avoids ChromaDB/local ML dependencies that are too large for Vercel.
_repo_indexes = {}

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768
EMBED_BATCH_SIZE = 32


def get_repo_id(repo_url: str) -> str:
    return hashlib.md5(repo_url.rstrip("/").encode()).hexdigest()[:12]


def _embed_documents(texts):
    time.sleep(0.8)
    result = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )
    return [array("f", e.values) for e in result.embeddings]


def _embed_query(text):
    time.sleep(0.8)
    result = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )
    return array("f", result.embeddings[0].values)


def _cosine_similarity(a, b):
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def store_code_in_vector_db(documents, repo_url: str):
    repo_id = get_repo_id(repo_url)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = []
    metadata = []

    for doc in documents:
        file_chunks = splitter.split_text(doc["content"])

        for chunk in file_chunks:
            if chunk.strip():
                chunks.append(chunk)
                metadata.append({
                    "file_name": doc["file_name"],
                    "repo_id": repo_id,
                })

    if not chunks:
        _repo_indexes[repo_id] = []
        return

    entries = []

    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch_chunks = chunks[start:start + EMBED_BATCH_SIZE]
        batch_vectors = _embed_documents(batch_chunks)

        for i, vector in enumerate(batch_vectors):
            entries.append({
                "text": batch_chunks[i],
                "embedding": vector,
                "metadata": metadata[start + i],
            })

    _repo_indexes[repo_id] = entries


def index_chunks_stream(chunks, file_name, repo_url):
    repo_id = get_repo_id(repo_url)

    existing = _repo_indexes.setdefault(repo_id, [])

    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch_chunks = chunks[start:start + EMBED_BATCH_SIZE]
        batch_vectors = _embed_documents(batch_chunks)

        for i, vector in enumerate(batch_vectors):
            existing.append({
                "text": batch_chunks[i],
                "embedding": vector,
                "metadata": {
                    "file_name": file_name,
                    "repo_id": repo_id,
                },
            })


def query_repository(question, repo_url):
    repo_id = get_repo_id(repo_url)
    entries = _repo_indexes.get(repo_id, [])

    if not entries:
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    query_vector = _embed_query(question)

    scored = []

    for entry in entries:
        score = _cosine_similarity(query_vector, entry["embedding"])
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]

    return {
        "documents": [[item[1]["text"] for item in top]],
        "metadatas": [[item[1]["metadata"] for item in top]],
        "distances": [[1.0 - item[0] for item in top]],
    }

