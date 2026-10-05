import os
import shutil
import stat
import hashlib
import tempfile
import zipfile

import requests

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "RepoMindAI/1.0",
    "X-GitHub-Api-Version": "2022-11-28",
}

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
    Returns repository size in KB. Logs warning for large repos.
    """
    owner, repo = _parse_repo(repo_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        response = requests.get(api_url, headers=GITHUB_HEADERS, timeout=10)

        if response.status_code != 200:
            print(f"SIZE CHECK: GitHub API returned {response.status_code}, skipping size gate.")
            return 0

        data = response.json()
        size_kb = int(data.get("size", 0))
        size_mb = size_kb // 1024

        print(f"SIZE CHECK: Repository total size is ~{size_mb} MB")

        if size_mb > 2000:
            print(f"SIZE CHECK WARNING: Large repository ({size_mb} MB). Proceeding with lightweight source ZIP archive download.")

        return size_kb

    except Exception as e:
        print(f"SIZE CHECK: Could not determine repo size: {e}")
        return 0


def get_repository_details(repo_url: str) -> dict:
    owner, repo = _parse_repo(repo_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(api_url, headers=GITHUB_HEADERS, timeout=15)

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


def remove_readonly(func, path, excinfo):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _safe_extract(zip_file: zipfile.ZipFile, destination: str):
    destination = os.path.abspath(destination)

    for member in zip_file.infolist():
        target = os.path.abspath(os.path.join(destination, member.filename))

        if not target.startswith(destination + os.sep):
            raise ValueError("Unsafe path found in repository archive")

    zip_file.extractall(destination)


def _purge_stale_clones(clones_dir: str):
    try:
        if os.path.exists(clones_dir):
            for item in os.listdir(clones_dir):
                item_path = os.path.join(clones_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
                except Exception:
                    pass
    except Exception:
        pass


def clone_repository(repo_url: str) -> str:
    """
    Downloads a GitHub repository as a ZIP archive and extracts it
    into the writable temporary directory used by Vercel.
    """

    owner, repo_name = _parse_repo(repo_url)

    clones_dir = os.path.join(tempfile.gettempdir(), "repomind_cloned_repos")
    _purge_stale_clones(clones_dir)
    os.makedirs(clones_dir, exist_ok=True)

    clean_url = repo_url.rstrip("/")
    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]

    url_hash = hashlib.md5(clean_url.encode()).hexdigest()[:8]

    folder = os.path.join(clones_dir, f"{repo_name}_{url_hash}")

    if os.path.isdir(folder):
        print(f"Repository already available: {folder}")
        return folder

    candidate_zip_urls = [
        f"https://codeload.github.com/{owner}/{repo_name}/zip/refs/heads/main",
        f"https://codeload.github.com/{owner}/{repo_name}/zip/refs/heads/master",
        f"https://api.github.com/repos/{owner}/{repo_name}/zipball",
    ]

    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        res = requests.get(api_url, headers=GITHUB_HEADERS, timeout=10)
        if res.status_code == 200:
            branch = res.json().get("default_branch")
            if branch:
                candidate_zip_urls.insert(0, f"https://codeload.github.com/{owner}/{repo_name}/zip/refs/heads/{branch}")
                candidate_zip_urls.insert(1, f"https://api.github.com/repos/{owner}/{repo_name}/zipball/{branch}")
    except Exception as e:
        print(f"GitHub default branch lookup skipped: {e}")

    archive_path = os.path.join(clones_dir, f"{repo_name}_{url_hash}.zip")
    extract_dir  = os.path.join(clones_dir, f"{repo_name}_{url_hash}_extract")

    print(f"Downloading repository archive for {owner}/{repo_name}...")

    downloaded = False
    for zip_url in candidate_zip_urls:
        try:
            shutil.rmtree(extract_dir, ignore_errors=True)
            shutil.rmtree(folder, ignore_errors=True)

            with requests.get(zip_url, headers=GITHUB_HEADERS, stream=True, timeout=30, allow_redirects=True) as response:
                if response.status_code == 200:
                    with open(archive_path, "wb") as archive:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                archive.write(chunk)
                    downloaded = True
                    print(f"Downloaded repository archive from: {zip_url}")
                    break
        except Exception as err:
            print(f"Failed download attempt from {zip_url}: {err}")

    if not downloaded or not os.path.exists(archive_path):
        raise ValueError(f"Could not download repository archive for '{owner}/{repo_name}'. Please verify the URL.")

    try:
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(archive_path, "r") as zip_file:
            _safe_extract(zip_file, extract_dir)

        entries = [
            os.path.join(extract_dir, name)
            for name in os.listdir(extract_dir)
        ]

        if len(entries) == 1 and os.path.isdir(entries[0]):
            shutil.move(entries[0], folder)
        else:
            shutil.move(extract_dir, folder)

        print(f"Repository extracted successfully: {folder}")
        return folder

    finally:
        try:
            if os.path.exists(archive_path):
                os.remove(archive_path)
        except Exception:
            pass

        if os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
