import os
import shutil
import stat
import hashlib
import tempfile
import zipfile

import requests


# ============================================================
# Repository Size Gate
# ============================================================

MAX_REPO_SIZE_MB = 500


def _parse_repo(repo_url: str):
    clean_url = repo_url.rstrip("/")

    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]

    parts = clean_url.split("/")

    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL")

    owner = parts[-2]
    repo = parts[-1]

    return owner, repo


def check_repo_size(repo_url: str) -> int:
    """
    Fetch repository size from GitHub API.

    Returns repository size in KB.
    Raises ValueError when repository exceeds MAX_REPO_SIZE_MB.
    """

    owner, repo = _parse_repo(repo_url)

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        response = requests.get(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            timeout=10,
        )

        if response.status_code != 200:
            print(
                f"SIZE CHECK: GitHub API returned "
                f"{response.status_code}, skipping size gate."
            )
            return 0

        data = response.json()
        size_kb = int(data.get("size", 0))
        size_mb = size_kb // 1024

        print(f"SIZE CHECK: Repository is ~{size_mb} MB")

        if size_kb > MAX_REPO_SIZE_MB * 1024:
            raise ValueError(
                f"Repository is too large ({size_mb} MB). "
                f"Maximum supported size is {MAX_REPO_SIZE_MB} MB."
            )

        return size_kb

    except ValueError:
        raise

    except Exception as e:
        print(f"SIZE CHECK: Could not determine repo size: {e}")
        return 0


# ============================================================
# Repository Details
# ============================================================

def get_repository_details(repo_url: str) -> dict:
    """
    Fetch basic repository metadata from GitHub API.
    """

    owner, repo = _parse_repo(repo_url)

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        timeout=15,
    )

    print(f"GitHub API URL: {api_url}")
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        return {"error": "Repository not found"}

    data = response.json()

    return {
        "name": data.get("name"),
        "owner": data.get("owner", {}).get("login"),
        "stars": data.get("stargazers_count", 0),
        "language": data.get("language"),
        "forks": data.get("forks_count", 0),
    }


# ============================================================
# Windows read-only file handler
# ============================================================

def remove_readonly(func, path, excinfo):
    """
    Error handler for shutil.rmtree on Windows.
    """

    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


# ============================================================
# Safe ZIP extraction
# ============================================================

def _safe_extract(zip_file: zipfile.ZipFile, destination: str):
    """
    Extract ZIP while preventing path traversal.
    """

    destination = os.path.abspath(destination)

    for member in zip_file.infolist():
        target = os.path.abspath(
            os.path.join(destination, member.filename)
        )

        if not target.startswith(destination + os.sep):
            raise ValueError("Unsafe path found in repository archive")

    zip_file.extractall(destination)


# ============================================================
# Download + Extract Repository
# ============================================================

def clone_repository(repo_url: str) -> str:
    """
    Downloads a GitHub repository as a ZIP archive and extracts it
    into the writable temporary directory used by Vercel.

    Returns the local path to the extracted repository.
    """

    owner, repo_name = _parse_repo(repo_url)

    clones_dir = os.path.join(
        tempfile.gettempdir(),
        "repomind_cloned_repos",
    )

    os.makedirs(clones_dir, exist_ok=True)

    clean_url = repo_url.rstrip("/")

    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]

    url_hash = hashlib.md5(
        clean_url.encode()
    ).hexdigest()[:8]

    folder = os.path.join(
        clones_dir,
        f"{repo_name}_{url_hash}",
    )

    # Reuse an already extracted repository in this invocation.
    if os.path.isdir(folder):
        print(f"Repository already available: {folder}")
        return folder

    api_url = f"https://api.github.com/repos/{owner}/{repo_name}"

    response = requests.get(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        timeout=15,
    )

    if response.status_code != 200:
        raise ValueError(
            f"GitHub repository could not be accessed "
            f"(HTTP {response.status_code})"
        )

    data = response.json()
    default_branch = data.get("default_branch", "main")

    print(f"GitHub default branch: {default_branch}")

    zip_url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo_name}/zipball/{default_branch}"
    )

    archive_path = os.path.join(
        clones_dir,
        f"{repo_name}_{url_hash}.zip",
    )

    extract_dir = os.path.join(
        clones_dir,
        f"{repo_name}_{url_hash}_extract",
    )

    print(f"Downloading repository archive: {repo_url}")

    try:
        shutil.rmtree(extract_dir, ignore_errors=True)
        shutil.rmtree(folder, ignore_errors=True)

        with requests.get(
            zip_url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            stream=True,
            timeout=60,
            allow_redirects=True,
        ) as response:

            if response.status_code != 200:
                raise ValueError(
                    f"Repository archive download failed "
                    f"(HTTP {response.status_code})"
                )

            with open(archive_path, "wb") as archive:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        archive.write(chunk)

        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(archive_path, "r") as zip_file:
            _safe_extract(zip_file, extract_dir)

        entries = [
            os.path.join(extract_dir, name)
            for name in os.listdir(extract_dir)
        ]

        # GitHub normally places everything inside one top-level folder.
        if len(entries) == 1 and os.path.isdir(entries[0]):
            extracted_root = entries[0]
            shutil.move(extracted_root, folder)
        else:
            # Fallback for archives without a single top-level folder.
            shutil.move(extract_dir, folder)

        print(f"Repository downloaded successfully: {folder}")

        return folder

    finally:
        try:
            if os.path.exists(archive_path):
                os.remove(archive_path)
        except Exception:
            pass

        # Only remove the temporary extraction directory if it still exists.
        if os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)

