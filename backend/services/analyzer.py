import os


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


# ============================================================
# Supported source / documentation file extensions
# ============================================================

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".html",
    ".css",
    ".json",
    ".md",
    ".txt",
    ".sh",
    ".yaml",
    ".yml",
    ".toml",
    ".vue",
    ".svelte",
    ".kt",
    ".swift",
    ".dart"
}


ALLOWED_NAMES = {
    "readme",
    "license",
    "dockerfile",
    "makefile",
    ".env.example",
    ".env.sample"
}


# ============================================================
# Binary + noise file detection
# ============================================================

BINARY_EXTENSIONS = {
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".ico", ".svg", ".webp", ".tiff", ".raw",
    # Audio / Video
    ".mp4", ".mp3", ".wav", ".avi", ".mov",
    ".mkv", ".flac", ".ogg", ".webm",
    # Archives
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".bz2", ".xz", ".dmg", ".iso",
    # Documents
    ".pdf", ".doc", ".docx", ".xls",
    ".xlsx", ".pptx", ".odt",
    # Compiled / binary artifacts
    ".exe", ".dll", ".so", ".dylib",
    ".wasm", ".pyc", ".pyo", ".class",
    ".o", ".a", ".lib",
    # Fonts
    ".ttf", ".woff", ".woff2", ".eot", ".otf",
    # Databases
    ".db", ".sqlite", ".sqlite3", ".mdb",
    # Build maps (large, unreadable)
    ".map",
}

NOISE_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "composer.lock",
    "gemfile.lock",
    "cargo.lock",
    "packages.lock.json",
    "shrinkwrap.yaml"
}


def is_processable_file(file_name: str, file_path: str) -> bool:
    """
    Returns False for:
      - Known binary extensions
      - Minified JS/CSS files (*.min.js, *.min.css)
      - Lock files (package-lock.json, yarn.lock, etc.)
      - Any file with null bytes in its first 512 bytes (binary sniff)
    """

    lower = os.path.basename(file_name).lower()

    # ----------------------------------------
    # Reject known binary extensions
    # ----------------------------------------

    if any(lower.endswith(ext) for ext in BINARY_EXTENSIONS):
        return False

    # ----------------------------------------
    # Reject minified files
    # ----------------------------------------

    if ".min.js" in lower or ".min.css" in lower:
        return False

    # ----------------------------------------
    # Reject known lock / noise filenames
    # ----------------------------------------

    if lower in NOISE_FILENAMES:
        return False

    # ----------------------------------------
    # Binary sniff — null bytes = binary file
    # ----------------------------------------

    try:
        with open(file_path, "rb") as f:
            sample = f.read(512)
        if b"\x00" in sample:
            return False
    except Exception:
        return False

    return True


# ============================================================
# Chunked file reader (Fix 2 — no full-file RAM load)
# ============================================================

MAX_FILE_SIZE_BYTES = 500_000   # 500 KB hard cap
CHUNK_SIZE_BYTES    = 8_192     # Read 8 KB at a time


def _read_file_chunked(file_path: str) -> str | None:
    """
    Reads a file in 8 KB chunks to avoid RAM spikes.
    Returns None if the file is too large, empty, or unreadable.
    """

    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
            print(f"EXTRACTOR: Skipping large file: {os.path.basename(file_path)}")
            return None

        parts = []

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            while True:
                chunk = f.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                parts.append(chunk)

        content = "".join(parts)
        return content if content.strip() else None

    except Exception as e:
        print(f"EXTRACTOR: Could not read {os.path.basename(file_path)}: {e}")
        return None


# ============================================================
# File walker — yields only processable code files
# ============================================================

def _walk_code_files(repo_path: str):
    """
    Yields (abs_path, rel_path) for every whitelisted, non-binary
    source file in the repository. Skips IGNORED_DIRS entirely.
    """

    for root, dirs, files in os.walk(repo_path):

        # Prune ignored directories in-place
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRS
        ]

        for file in files:

            lower_file = file.lower()

            has_allowed_extension = any(
                lower_file.endswith(ext)
                for ext in ALLOWED_EXTENSIONS
            )

            is_allowed_name = (
                lower_file in ALLOWED_NAMES
                or lower_file.startswith("readme")
                or lower_file.startswith("license")
            )

            if not has_allowed_extension and not is_allowed_name:
                continue

            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, repo_path)

            yield abs_path, rel_path


# ============================================================
# Repository Statistics
# ============================================================

def analyze_repository(path: str) -> dict:
    """
    Walks the repository and counts files by language.
    Skips binary/noise files and ignored directories.
    """

    print("ANALYZER: Starting repository analysis")

    total_files       = 0
    python_files      = 0
    javascript_files  = 0
    typescript_files  = 0

    for root, dirs, files in os.walk(path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRS
        ]

        for file in files:

            total_files += 1
            lower_file = file.lower()

            if lower_file.endswith(".py"):
                python_files += 1

            elif lower_file.endswith((".js", ".jsx")):
                javascript_files += 1

            elif lower_file.endswith((".ts", ".tsx")):
                typescript_files += 1

    print("ANALYZER: Analysis completed")

    return {
        "total_files":       total_files,
        "python_files":      python_files,
        "javascript_files":  javascript_files,
        "typescript_files":  typescript_files
    }


def _file_priority(rel_path: str) -> int:
    lower = rel_path.lower()
    base = os.path.basename(lower)
    if base.startswith("readme") or base in {"package.json", "requirements.txt", "main.py", "index.js", "app.jsx", "app.tsx", "dockerfile"}:
        return 0
    if "/" not in rel_path and "\\" not in rel_path:
        return 1
    depth = rel_path.count("/") + rel_path.count("\\")
    return 2 + depth


# ============================================================
# Streaming Index Pipeline
# ============================================================

def stream_and_index(
    repo_path: str,
    repo_url:  str,
    job_id:    str,
    jobs:      dict
) -> dict:
    """
    Streaming pipeline: read one file → split → embed → store → repeat.

    Bounded to MAX_TOTAL_CHUNKS (64 chunks = 2 Gemini embedding batches)
    to prevent Gemini API 429 RESOURCE_EXHAUSTED free tier rate limits.
    """

    from ai_engine.rag import index_batched_chunks
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    print("EXTRACTOR: Starting streaming extraction")

    MAX_TOTAL_CHUNKS = 64

    all_files = list(_walk_code_files(repo_path))
    all_files.sort(key=lambda item: _file_priority(item[1]))

    total     = max(len(all_files), 1)
    processed = 0

    all_chunks = []
    all_metadatas = []

    for abs_path, rel_path in all_files:
        if len(all_chunks) >= MAX_TOTAL_CHUNKS:
            break

        if not is_processable_file(rel_path, abs_path):
            processed += 1
            continue

        content = _read_file_chunked(abs_path)
        if content is None:
            processed += 1
            continue

        chunks = splitter.split_text(content)
        for c in chunks:
            if c.strip():
                all_chunks.append(c)
                all_metadatas.append({"file_name": rel_path})
                if len(all_chunks) >= MAX_TOTAL_CHUNKS:
                    break

        processed += 1
        jobs[job_id]["progress"] = int(processed / total * 50)
        del content, chunks

    print(f"EXTRACTOR: Scanned {processed} files. Batch indexing {len(all_chunks)} chunks...")
    index_batched_chunks(all_chunks, all_metadatas, repo_url, job_id, jobs)

    print(f"EXTRACTOR: Done. {processed} files, {len(all_chunks)} chunks indexed.")

    return {
        "message":       "Code indexed successfully",
        "files_scanned": processed,
        "chunks_stored": len(all_chunks)
    }


# ============================================================
# Legacy extract_code_files — kept for backward compatibility
# ============================================================

def extract_code_files(path: str) -> list[dict]:
    """
    Original function — kept for compatibility.
    New code should call stream_and_index() instead.
    """

    documents = []

    for abs_path, rel_path in _walk_code_files(path):

        if not is_processable_file(rel_path, abs_path):
            continue

        content = _read_file_chunked(abs_path)

        if content is None:
            continue

        documents.append({
            "file_name": rel_path,
            "content":   content
        })

    print(f"EXTRACTOR: Finished. Files extracted: {len(documents)}")

    return documents