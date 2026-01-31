from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.report.report_builder import build_report, build_static_report
from app.core.ai_service import optimize_with_ai
from app.docker.client import get_docker_client
from app.core.github_service import extract_repo_info, find_dockerfile, get_file_content, create_pull_request, full_pr_workflow
from fastapi import HTTPException
import requests

router = APIRouter()


@router.get("/containers")
def list_containers():
    client = get_docker_client()
    containers = client.containers.list(all=True)
    results = []

    for c in containers:
        try:
            image = client.images.get(c.image.id)
            image_size_mb = round(image.attrs["Size"] / (1024 * 1024), 2)

            memory_usage_mb = 0.0
            if c.status == "running":
                stats = c.stats(stream=False)
                mem = stats["memory_stats"].get("usage", 0)
                memory_usage_mb = round(mem / (1024 * 1024), 2)

            results.append({
                "id": c.short_id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.id,
                "status": c.status,
                "image_size_mb": image_size_mb,
                "memory_usage_mb": memory_usage_mb,
            })

        except Exception as e:
            print(f"[containers] failed for {c.name}: {e}")

    return results



@router.get("/image/report")
def image_report(image: str):
    return build_report(image)


class DockerfileRequest(BaseModel):
    content: str



@router.post("/analyze-dockerfile")
def analyze_dockerfile(request: DockerfileRequest):
    return build_static_report(request.content)


class AIOptimizeRequest(BaseModel):
    image_context: dict
    dockerfile_content: Optional[str] = None


@router.post("/ai-optimize")
def ai_optimize(request: AIOptimizeRequest):
    return optimize_with_ai(request.image_context, request.dockerfile_content)


class GitHubScanRequest(BaseModel):
    url: str

@router.post("/scan-github")
def scan_github(request: GitHubScanRequest):
    owner, repo, branch = extract_repo_info(request.url)
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    
    path = find_dockerfile(owner, repo)
    if not path:
        raise HTTPException(status_code=404, detail="Dockerfile not found in repository root")
    
    content = get_file_content(owner, repo, path)
    if not content:
        raise HTTPException(status_code=500, detail="Failed to fetch Dockerfile content")
    
    # Use the unified static report builder (includes Trivy + AI)
    report = build_static_report(content)
    
    # Map for frontend compatibility if needed, or just return the full report
    # We add GitHub metadata to the report
    report.update({
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "path": path,
        "original_content": content,
        "url": request.url # Added to ensure PR creation has the URL
    })
    
    # Ensure ResultViewer can find the AI result
    if "recommendation" in report and "dockerfile" in report["recommendation"]:
        report["optimization"] = report["recommendation"]["dockerfile"]
    
    return report

class CreatePRRequest(BaseModel):
    url: str
    optimized_content: str
    path: Optional[str] = "Dockerfile"
    branch_name: Optional[str] = "optimize-dockerfile"
    base_branch: Optional[str] = None

@router.post("/create-pr")
def create_pr(request: CreatePRRequest):
    owner, repo, branch = extract_repo_info(request.url)
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    
    try:
        pr_link = full_pr_workflow(
            owner=owner,
            repo=repo,
            dockerfile_path=request.path,
            new_content=request.optimized_content,
            branch_name=request.branch_name,
            base_branch=request.base_branch
        )
        return {"message": f"Successfully created PR: {pr_link}" if "github.com" in pr_link else pr_link}
    except requests.exceptions.HTTPError as e:
        error_data = {}
        try:
            error_data = e.response.json()
        except:
            pass
        msg = error_data.get("message", str(e))
        print(f"GitHub API Error: {msg}")
        raise HTTPException(status_code=400, detail=f"GitHub Error: {msg}")
    except Exception as e:
        print(f"PR Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
