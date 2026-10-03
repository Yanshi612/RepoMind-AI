import os
import shutil
import hashlib

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CHROMA_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)

client = None
collection = None


def _make_client():
    return chromadb.PersistentClient(
        path=CHROMA_PATH
    )


def _make_collection(c):
    try:
        return c.get_collection(
            name="repo_code"
        )
    except Exception:
        return c.create_collection(
            name="repo_code"
        )


def _init_chroma():
    global client
    global collection

    try:
        client = _make_client()
        collection = _make_collection(client)
        collection.count()

    except Exception as e:

        error_text = str(e).lower()

        if (
            "hnsw" in error_text
            or "segment" in error_text
            or "compaction" in error_text
        ):

            print(
                f"[rag] ChromaDB index corrupted: {e}"
            )

            shutil.rmtree(
                CHROMA_PATH,
                ignore_errors=True
            )

            client = _make_client()
            collection = _make_collection(client)

            print(
                "[rag] ChromaDB reinitialised successfully."
            )

        else:
            raise


def get_collection():

    global client
    global collection

    if collection is None:

        print(
            "RAG: Initializing ChromaDB..."
        )

        _init_chroma()

        print(
            "RAG: ChromaDB ready."
        )

    return collection


_embedding_model = None


def get_embedding_model():

    global _embedding_model

    if _embedding_model is None:

        print(
            "RAG: Loading embedding model..."
        )

        _embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )

        print(
            "RAG: Embedding model ready."
        )

    return _embedding_model


def get_repo_id(repo_url: str) -> str:

    return hashlib.md5(
        repo_url.rstrip("/").encode()
    ).hexdigest()[:12]


def index_chunks_stream(
    chunks: list[str],
    file_name: str,
    repo_url: str
) -> None:

    repo_id = get_repo_id(repo_url)

    model = get_embedding_model()

    db_collection = get_collection()

    EMBEDDING_BATCH_SIZE = 16

    for start in range(
        0,
        len(chunks),
        EMBEDDING_BATCH_SIZE
    ):

        batch = chunks[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        if not batch:
            continue

        vectors = model.encode(
            batch,
            batch_size=8,
            show_progress_bar=False
        )

        ids = [
            f"{repo_id}_"
            f"{hashlib.md5(
                f'{file_name}_{start + i}'.encode()
            ).hexdigest()[:10]}"
            for i in range(
                len(batch)
            )
        ]

        embeddings = [
            vector.tolist()
            for vector in vectors
        ]

        metadatas = [
            {
                "repo_id": repo_id,
                "file": file_name
            }
            for _ in batch
        ]

        db_collection.upsert(
            ids=ids,
            documents=batch,
            embeddings=embeddings,
            metadatas=metadatas
        )

        del vectors
        del embeddings


def store_code_in_vector_db(
    documents: list[dict],
    repo_url: str
) -> dict:

    repo_id = get_repo_id(repo_url)

    print(
        f"Repository ID: {repo_id}"
    )

    db_collection = get_collection()

    try:

        db_collection.delete(
            where={
                "repo_id": repo_id
            }
        )

        print(
            "Old repository vectors removed."
        )

    except Exception as e:

        print(
            f"No old vectors to remove: {e}"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    total_chunks = 0

    for doc in documents:

        chunks = splitter.split_text(
            doc["content"]
        )

        if chunks:

            index_chunks_stream(
                chunks,
                doc["file_name"],
                repo_url
            )

            total_chunks += len(chunks)

    if total_chunks == 0:

        return {
            "message": "No code files found.",
            "chunks": 0,
            "repo_id": repo_id
        }

    print(
        "Repository stored successfully."
    )

    return {
        "message": "Code stored successfully",
        "chunks": total_chunks,
        "repo_id": repo_id
    }


def query_repository(
    question: str,
    repo_url: str
) -> dict:

    repo_id = get_repo_id(repo_url)

    model = get_embedding_model()

    db_collection = get_collection()

    print(
        f"RAG: Searching repository {repo_id}"
    )

    print(
        f"RAG: Question: {question}"
    )

    question_embedding = (
        model
        .encode(question)
        .tolist()
    )

    results = db_collection.query(
        query_embeddings=[
            question_embedding
        ],
        n_results=5,
        where={
            "repo_id": repo_id
        }
    )

    print(
        "RAG: Relevant chunks found:",
        len(
            results.get(
                "documents",
                [[]]
            )[0]
        )
    )

    return results
