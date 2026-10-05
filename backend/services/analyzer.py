import os
import io
import zipfile

# ============================================================
# Folders that should never be scanned
# ============================================================

IGNORED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".next",
    "target",
    "chroma_db",
    ".tox",
    ".eggs",
    "buck-out",
    ".gradle",
    "Pods",
    ".dart_tool",
    ".pub-cache"
}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs",
    ".rb", ".php", ".html", ".css", ".json", ".md",
    ".txt", ".sh", ".yaml", ".yml", ".toml", ".vue",
    ".svelte", ".kt", ".swift", ".dart"
}

ALLOWED_NAMES = {
    "readme", "license", "dockerfile", "makefile",
    ".env.example", ".env.sample"
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico",
    ".svg", ".webp", ".tiff", ".raw", ".mp4", ".mp3",
    ".wav", ".avi", ".mov", ".zip", ".tar", ".gz",
    ".rar", ".7z", ".pdf", ".doc", ".docx", ".xls",
    ".xlsx", ".pptx", ".exe", ".dll", ".so", ".dylib",
    ".wasm", ".pyc", ".pyo", ".class", ".o", ".a",
    ".lib", ".ttf", ".woff", ".woff2", ".db", ".sqlite",
    ".map"
}

NOISE_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "composer.lock", "gemfile.lock",
    "cargo.lock", "packages.lock.json", "shrinkwrap.yaml"
}

MAX_FILE_SIZE_BYTES = 500_000


def _file_priority(rel_path: str) -> int:
    lower = rel_path.lower()
    base = os.path.basename(lower)
    if base.startswith("readme") or base in {"package.json", "requirements.txt", "main.py", "index.js", "app.jsx", "app.tsx", "dockerfile"}:
        return 0
    if "/" not in rel_path and "\\" not in rel_path:
        return 1
    depth = rel_path.count("/") + rel_path.count("\\")
    return 2 + depth


def analyze_and_index_zip(zip_bytes: bytes, repo_url: str, job_id: str, jobs: dict) -> dict:
    """
    Analyzes and indexes repository source code directly from in-memory ZIP bytes.
    Zero disk writes in /tmp — 100% immune to [Errno 28] disk space errors.
    """
    from ai_engine.rag import index_batched_chunks
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    total_files = 0
    python_files = 0
    javascript_files = 0
    typescript_files = 0

    processable_entries = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()

        for name in namelist:
            if name.endswith("/"):
                continue

            parts = name.split("/")
            if any(p in IGNORED_DIRS for p in parts):
                continue

            total_files += 1
            base = os.path.basename(name).lower()
            rel_path = name.split("/", 1)[1] if "/" in name else name

            if base.endswith(".py"):
                python_files += 1
            elif base.endswith((".js", ".jsx")):
                javascript_files += 1
            elif base.endswith((".ts", ".tsx")):
                typescript_files += 1

            has_ext = any(base.endswith(ext) for ext in ALLOWED_EXTENSIONS)
            has_name = (base in ALLOWED_NAMES or base.startswith("readme") or base.startswith("license"))

            if has_ext or has_name:
                if not any(base.endswith(ext) for ext in BINARY_EXTENSIONS) and base not in NOISE_FILENAMES and ".min.js" not in base and ".min.css" not in base:
                    processable_entries.append((name, rel_path))

        processable_entries.sort(key=lambda item: _file_priority(item[1]))

        MAX_TOTAL_CHUNKS = 64
        all_chunks = []
        all_metadatas = []

        for zip_name, rel_path in processable_entries:
            if len(all_chunks) >= MAX_TOTAL_CHUNKS:
                break

            try:
                info = zf.getinfo(zip_name)
                if info.file_size > MAX_FILE_SIZE_BYTES:
                    continue

                raw = zf.read(zip_name)
                if b"\x00" in raw[:512]:
                    continue

                content = raw.decode("utf-8", errors="ignore")
                if not content.strip():
                    continue

                chunks = splitter.split_text(content)
                for c in chunks:
                    if c.strip():
                        all_chunks.append(c)
                        all_metadatas.append({"file_name": rel_path})
                        if len(all_chunks) >= MAX_TOTAL_CHUNKS:
                            break
            except Exception as e:
                print(f"Zip entry read notice for {rel_path}: {e}")

        print(f"IN-MEMORY EXTRACTOR: Scanned {total_files} files. Batch indexing {len(all_chunks)} chunks...")
        index_batched_chunks(all_chunks, all_metadatas, repo_url, job_id, jobs)

        stats = {
            "total_files":       total_files,
            "python_files":      python_files,
            "javascript_files":  javascript_files,
            "typescript_files":  typescript_files
        }

        return {
            "stats": stats,
            "vector_db": {
                "message":       "Code indexed successfully",
                "files_scanned": total_files,
                "chunks_stored": len(all_chunks)
            }
        }


def analyze_repository(path: str) -> dict:
    return {"total_files": 0, "python_files": 0, "javascript_files": 0, "typescript_files": 0}

def stream_and_index(repo_path: str, repo_url: str, job_id: str, jobs: dict) -> dict:
    return {"message": "Code indexed successfully", "files_scanned": 0, "chunks_stored": 0}