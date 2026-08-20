import os
import shutil
import stat
import hashlib
import requests

from git import Repo


# ============================================================
# Repository Size Gate
# ============================================================

MAX_REPO_SIZE_MB = 500   # Repos larger than this are rejected


def check_repo_size(repo_url: str) -> int:
    """
    Fetches repo metadata from GitHub API and raises ValueError
    if the repository exceeds MAX_REPO_SIZE_MB.

    Returns the repo size in KB so callers can log it.
    """

    parts = repo_url.rstrip("/").split("/")
    owner = parts[-2]
    repo  = parts[-1].removesuffix(".git")

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            # Don't block the clone if API is unavailable — just warn
            print(f"SIZE CHECK: GitHub API returned {response.status_code}, skipping size gate.")
            return 0

        data    = response.json()
        size_kb = data.get("size", 0)
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
        # Network error — don't block the clone
        print(f"SIZE CHECK: Could not determine repo size: {e}")
        return 0


# ============================================================
# Repository Details
# ============================================================

def get_repository_details(repo_url: str) -> dict:
    """
    Fetches basic repository metadata from the GitHub API.
    """

    parts = repo_url.rstrip("/").split("/")
    owner = parts[-2]
    repo  = parts[-1].removesuffix(".git")

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(api_url, timeout=15)

    print(f"GitHub API URL: {api_url}")
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        return {"error": "Repository not found"}

    data = response.json()

    return {
        "name":     data["name"],
        "owner":    data["owner"]["login"],
        "stars":    data["stargazers_count"],
        "language": data["language"],
        "forks":    data["forks_count"]
    }


# ============================================================
# Windows read-only file handler
# ============================================================

def remove_readonly(func, path, excinfo):
    """
    Error handler for shutil.rmtree on Windows.
    Clears the read-only attribute and retries.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


# ============================================================
# Clone Repository (shallow + single-branch)
# ============================================================

def clone_repository(repo_url: str) -> str:
    """
    Clones a GitHub repository with --depth 1 --single-branch to
    minimize download size and time.

    If the repo already exists locally, does a shallow fetch instead
    of a full pull (which would download entire history).

    Returns the local path to the cloned repository.
    """

    base_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    clones_dir = os.path.join(base_dir, "cloned_repos")

    os.makedirs(clones_dir, exist_ok=True)

    # ----------------------------------------
    # Build a deterministic folder name
    # ----------------------------------------

    clean_url = repo_url.rstrip("/")

    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]

    repo_name = clean_url.split("/")[-1]
    url_hash  = hashlib.md5(clean_url.encode()).hexdigest()[:8]
    folder    = os.path.join(clones_dir, f"{repo_name}_{url_hash}")

    # ----------------------------------------
    # Repository already exists — update it
    # ----------------------------------------

    if os.path.exists(folder):

        print(f"Repository already exists: {folder}")

        try:
            repo = Repo(folder)

            print("Fetching latest changes (shallow)...")

            # FIX: fetch only the latest commit — don't pull full history
            repo.remotes.origin.fetch(depth=1, update_shallow=True)
            repo.git.reset("--hard", "FETCH_HEAD")

            print("Repository updated successfully.")
            return folder

        except Exception as e:

            print(f"Existing repository is corrupted: {e}")
            print("Removing and re-cloning...")

            try:
                shutil.rmtree(folder, onerror=remove_readonly)
            except Exception as delete_error:
                print(f"Could not delete repository: {delete_error}")
                raise

    # ----------------------------------------
    # Fresh clone — shallow + single-branch
    # ----------------------------------------

    print(f"Cloning repository: {repo_url}")
    print(f"Destination:        {folder}")

    Repo.clone_from(
        repo_url,
        folder,
        depth=1,             # Shallow clone — latest commit only
        single_branch=True   # Skip all other branches
    )

    print("Repository cloned successfully.")

    return folder