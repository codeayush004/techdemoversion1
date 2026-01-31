import requests
import base64
import os
import re
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

def get_token():
    return os.getenv("GITHUB_TOKEN")

def extract_repo_info(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts owner, repo name, and optional branch from a GitHub URL.
    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch
    - https://github.com/owner/repo/blob/branch/path
    """
    # Pattern to match owner, repo, and optional branch
    pattern = r"github\.com/([^/]+)/([^/.]+?)(?:/(?:tree|blob)/([^/]+))?(?:\.git)?(?:$|/)"
    match = re.search(pattern, url)
    if match:
        owner = match.group(1)
        repo = match.group(2).removesuffix(".git")
        branch = match.group(3)
        return owner, repo, branch
    return None, None, None

def get_headers():
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    token = get_token()
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def find_dockerfile(owner: str, repo: str) -> Optional[str]:
    """
    Searches for a Dockerfile in the repository root.
    Returns the path if found, else None.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        contents = response.json()
        for item in contents:
            if item["type"] == "file" and item["name"].lower() == "dockerfile":
                return item["path"]
    return None

def get_file_content(owner: str, repo: str, path: str) -> Optional[str]:
    """
    Fetches the content of a file from a GitHub repository.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        if "content" in data:
            # GitHub API returns base64 encoded content
            content_decoded = base64.b64decode(data["content"]).decode("utf-8")
            return content_decoded
    return None

def create_pull_request(owner: str, repo: str, title: str, body: str, head: str, base: str = "main"):
    """
    Creates a pull request on GitHub.
    """
    if not get_token():
        raise Exception("GITHUB_TOKEN is required to create a PR")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
    response = requests.post(url, headers=get_headers(), json=payload)
    return response

import time

def get_authenticated_user() -> str:
    """Gets the login name of the authenticated user."""
    url = "https://api.github.com/user"
    resp = requests.get(url, headers=get_headers())
    resp.raise_for_status()
    return resp.json()["login"]

def fork_repo(owner: str, repo: str):
    """Forks a repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    resp = requests.post(url, headers=get_headers())
    resp.raise_for_status()
    return resp.json()

def full_pr_workflow(owner: str, repo: str, dockerfile_path: str, new_content: str, branch_name: str = "optimize-dockerfile", base_branch: str = None):
    """
    Executes the full workflow:
    1. Check for write access. If no, fork.
    2. Create a new branch on the (forked) repo.
    3. Commit the new Dockerfile.
    4. Create the PR on the original repo.
    """
    if not get_token():
        raise Exception("GITHUB_TOKEN is required for this operation")

    headers = get_headers()
    current_user = get_authenticated_user()
    
    # 1. Check permissions
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_resp = requests.get(repo_url, headers=headers)
    repo_resp.raise_for_status()
    repo_data = repo_resp.json()
    
    can_write = repo_data.get("permissions", {}).get("push", False)
    default_branch = base_branch or repo_data["default_branch"]

    target_owner = owner
    if not can_write:
        fork_repo(owner, repo)
        target_owner = current_user
        # Wait for fork to be ready (up to 10 seconds)
        for i in range(5):
             time.sleep(2)
             check_url = f"https://api.github.com/repos/{target_owner}/{repo}"
             c_resp = requests.get(check_url, headers=headers)
             if c_resp.status_code == 200:
                 break

    # 2. Get Base SHA from TARGET repo (ensures it's ready)
    ref_url = f"https://api.github.com/repos/{target_owner}/{repo}/git/refs/heads/{default_branch}"
    ref_resp = requests.get(ref_url, headers=headers)
    if ref_resp.status_code != 200:
        # Fallback to upstream
        ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{default_branch}"
        ref_resp = requests.get(ref_url, headers=headers)
    
    ref_resp.raise_for_status()
    base_sha = ref_resp.json()["object"]["sha"]

    # 3. Create New Branch on TARGET repo
    new_ref_url = f"https://api.github.com/repos/{target_owner}/{repo}/git/refs"
    new_ref_payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    }
    new_ref_resp = requests.post(new_ref_url, headers=headers, json=new_ref_payload)
    if new_ref_resp.status_code not in [201, 422]:
        new_ref_resp.raise_for_status()

    # 4. Get Current File SHA from target repo and branch
    file_url = f"https://api.github.com/repos/{target_owner}/{repo}/contents/{dockerfile_path}"
    file_resp = requests.get(f"{file_url}?ref={branch_name}", headers=headers)
    if file_resp.status_code != 200:
        # Fallback to upstream version
        file_resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{dockerfile_path}", headers=headers)
    
    file_resp.raise_for_status()
    file_sha = file_resp.json()["sha"]

    # 5. Commit File Update to TARGET repo
    put_payload = {
        "message": "Optimize Dockerfile with AI",
        "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "sha": file_sha,
        "branch": branch_name
    }
    put_resp = requests.put(file_url, headers=headers, json=put_payload)
    put_resp.raise_for_status()

    # 6. Create PR on ORIGINAL repo
    head_param = f"{target_owner}:{branch_name}" if target_owner != owner else branch_name
    
    pr_resp = create_pull_request(
        owner, repo,
        title="✨ Optimized Dockerfile",
        body="This Pull Request introduces an industry-ready, secure, and optimized Dockerfile generated by the Docker Container Optimizer.",
        head=head_param,
        base=default_branch
    )
    
    if pr_resp.status_code == 201:
        return pr_resp.json()["html_url"]
    else:
        data = pr_resp.json()
        error_msg = data.get("errors", [{}])[0].get("message", "PR creation failed or already exists")
        if "already exists" in error_msg:
             try:
                 list_pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?head={head_param}&state=open"
                 l_resp = requests.get(list_pr_url, headers=headers)
                 if l_resp.status_code == 200 and len(l_resp.json()) > 0:
                     return l_resp.json()[0]["html_url"]
             except: pass
        return error_msg
