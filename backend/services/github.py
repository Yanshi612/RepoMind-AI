import os
import io
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


def download_repo_zip_bytes(repo_url: str) -> bytes:
    """
    Downloads a GitHub repository ZIP archive into RAM (in-memory bytes).
    Zero disk usage in /tmp.
    """
    owner, repo_name = _parse_repo(repo_url)

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

    for zip_url in candidate_zip_urls:
        try:
            res = requests.get(zip_url, headers=GITHUB_HEADERS, timeout=30, allow_redirects=True)
            if res.status_code == 200 and len(res.content) > 0:
                print(f"In-memory ZIP download successful from: {zip_url} ({len(res.content)} bytes)")
                return res.content
        except Exception as err:
            print(f"In-memory download attempt from {zip_url} failed: {err}")

    raise ValueError(f"Could not download repository archive for '{owner}/{repo_name}'. Please verify the URL.")


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


def clone_repository(repo_url: str) -> str:
    """Legacy helper kept for backward compatibility."""
    return ""
