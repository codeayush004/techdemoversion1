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
    # Handles .git suffix and repo names with dots
    pattern = r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/(?:tree|blob)/([^/]+))?(?:$|/)"
    match = re.search(pattern, url)
    if match:
        owner = match.group(1)
        repo = match.group(2).removesuffix(".git")
        branch = match.group(3)
        return owner, repo, branch
    return None, None, None

def get_headers(token: Optional[str] = None):
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    # Priority: passed token > environment token
    active_token = token or get_token()
    if active_token:
        headers["Authorization"] = f"token {active_token}"
    return headers

def find_all_dockerfiles(owner: str, repo: str, token: Optional[str] = None) -> list[str]:
    """
    Recursively searches for all Dockerfiles in a repository using the Trees API.
    Returns a list of paths.
    """
    # 1. Get the default branch and its latest commit SHA
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_resp = requests.get(repo_url, headers=get_headers(token))
    if repo_resp.status_code != 200:
        return []
    
    default_branch = repo_resp.json().get("default_branch", "main")
    
    # 2. Get the recursive tree
    # We use recursive=1 to get the entire tree in one go (limit 100k entries)
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    tree_resp = requests.get(tree_url, headers=get_headers(token))
    
    if tree_resp.status_code != 200:
        return []

    dockerfiles = []
    tree_data = tree_resp.json()
    for item in tree_data.get("tree", []):
        if item["type"] == "blob" and item["path"].split("/")[-1].lower() == "dockerfile":
            dockerfiles.append(item["path"])
            
    return sorted(dockerfiles)

            


def get_file_content(owner: str, repo: str, path: str, token: Optional[str] = None) -> Optional[str]:
    """
    Fetches the content of a file from a GitHub repository.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url, headers=get_headers(token))
    
    if response.status_code == 200:
        data = response.json()
        if "content" in data:
            # GitHub API returns base64 encoded content
            content_decoded = base64.b64decode(data["content"]).decode("utf-8")
            return content_decoded
    return None

def create_pull_request(owner: str, repo: str, title: str, body: str, head: str, base: str = "main", token: Optional[str] = None):
    """
    Creates a pull request on GitHub.
    """
    active_token = token or get_token()
    if not active_token:
        raise Exception("GITHUB_TOKEN or user token is required to create a PR")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
    response = requests.post(url, headers=get_headers(token), json=payload)
    return response

import time

def get_authenticated_user(token: str) -> str:
    """Gets the login name of the authenticated user."""
    url = "https://api.github.com/user"
    resp = requests.get(url, headers=get_headers(token))
    resp.raise_for_status()
    return resp.json()["login"]

def fork_repo(owner: str, repo: str, token: Optional[str] = None):
    """Forks a repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    resp = requests.post(url, headers=get_headers(token))
    resp.raise_for_status()
    return resp.json()

def full_bulk_pr_workflow(owner: str, repo: str, updates: list[dict], branch_name: str = "optimize-all-services", base_branch: str = None, pr_title: str = None, commit_message: str = None, token: Optional[str] = None):
    """
    Updates multiple files in a single commit and creates one PR.
    updates: list of {"path": str, "content": str}
    """
    active_token = token or get_token()
    if not active_token:
        raise Exception("GITHUB_TOKEN or user token is required for this operation")

    headers = get_headers(token)
    current_user = get_authenticated_user(active_token)
    
    # 1. Check permissions & Fork if needed
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
        for i in range(5):
             time.sleep(2)
             if requests.get(f"https://api.github.com/repos/{target_owner}/{repo}", headers=headers).status_code == 200:
                 break

    # 2. Get Base Branch SHA
    ref_url = f"https://api.github.com/repos/{target_owner}/{repo}/git/refs/heads/{default_branch}"
    ref_resp = requests.get(ref_url, headers=headers)
    if ref_resp.status_code != 200:
        ref_resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{default_branch}", headers=headers)
    ref_resp.raise_for_status()
    base_sha = ref_resp.json()["object"]["sha"]

    # 3. Create Blobs & Tree
    # We create a new tree starting from the base_sha's tree
    # First, get the tree SHA of the base commit
    commit_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{base_sha}"
    commit_resp = requests.get(commit_url, headers=headers)
    commit_resp.raise_for_status()
    base_tree_sha = commit_resp.json()["tree"]["sha"]

    tree_items = []
    for update in updates:
        tree_items.append({
            "path": update["path"],
            "mode": "100644",
            "type": "blob",
            "content": update["content"]
        })

    # Create the new tree
    create_tree_url = f"https://api.github.com/repos/{target_owner}/{repo}/git/trees"
    tree_payload = {
        "base_tree": base_tree_sha,
        "tree": tree_items
    }
    tree_resp = requests.post(create_tree_url, headers=headers, json=tree_payload)
    tree_resp.raise_for_status()
    new_tree_sha = tree_resp.json()["sha"]

    # 4. Create Commit
    commit_payload = {
        "message": commit_message or "Bulk optimization of multiple services",
        "tree": new_tree_sha,
        "parents": [base_sha]
    }
    commit_resp = requests.post(f"https://api.github.com/repos/{target_owner}/{repo}/git/commits", headers=headers, json=commit_payload)
    commit_resp.raise_for_status()
    new_commit_sha = commit_resp.json()["sha"]

    # 5. Update or Create Branch Ref
    ref_path = f"refs/heads/{branch_name}"
    ref_url = f"https://api.github.com/repos/{target_owner}/{repo}/git/{ref_path}"
    ref_check = requests.get(ref_url, headers=headers)
    
    if ref_check.status_code == 200:
        # Update existing
        requests.patch(ref_url, headers=headers, json={"sha": new_commit_sha, "force": True}).raise_for_status()
    else:
        # Create new
        requests.post(f"https://api.github.com/repos/{target_owner}/{repo}/git/refs", headers=headers, json={"ref": ref_path, "sha": new_commit_sha}).raise_for_status()

    # 6. Create PR
    head_param = f"{target_owner}:{branch_name}" if target_owner != owner else branch_name
    pr_resp = create_pull_request(
        owner, repo,
        title=pr_title or "✨ Bulk Service Optimization",
        body="This Pull Request introduces security and performance optimizations across multiple services (frontend/backend) in the repository.",
        head=head_param,
        base=default_branch
    )
    
    if pr_resp.status_code == 201:
        return pr_resp.json()["html_url"]
    else:
        return pr_resp.json().get("errors", [{}])[0].get("message", "PR creation failed")
