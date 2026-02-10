from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.report.report_builder import build_report, build_static_report
from app.docker.client import get_docker_client
from app.core.github_service import extract_repo_info, get_file_content, full_bulk_pr_workflow, find_all_dockerfiles
from fastapi import HTTPException
from app.core.registry_service import scan_registry_image

router = APIRouter()


@router.get("/containers")
def list_containers():
    client = get_docker_client()
    containers = client.containers.list(all=True)
    results = []

    for c in containers:
        try:
            # Optimize: Try to get size from attributes directly to avoid extra image fetch
            image_size_mb = 0.0
            try:
                if hasattr(c.image, "attrs") and "Size" in c.image.attrs:
                    image_size_mb = round(c.image.attrs["Size"] / (1024 * 1024), 2)
                else:
                    # Fallback if attrs missing
                    img = client.images.get(c.image.id)
                    image_size_mb = round(img.attrs["Size"] / (1024 * 1024), 2)
            except: pass

            # NOTE: We skip c.stats(stream=False) here because it is too slow (blocks for ~1s per container)
            # Memory usage will be fetched only during deep analysis.
            results.append({
                "id": c.short_id,
                "name": c.name,
                "image": c.image.tags[0] if (hasattr(c.image, "tags") and c.image.tags) else c.short_id,
                "status": c.status,
                "image_size_mb": image_size_mb,
            })

        except Exception:
            continue

    return results



class RuntimeScanRequest(BaseModel):
    image: str
    id: Optional[str] = None
    dockerfile_content: Optional[str] = None

@router.post("/image/report")
def image_report(request: RuntimeScanRequest):
    return build_report(request.image, request.dockerfile_content, container_id=request.id)


class DockerfileRequest(BaseModel):
    content: str

@router.post("/analyze-dockerfile")
def analyze_dockerfile(request: DockerfileRequest):
    return build_static_report(request.content)


class GitHubScanRequest(BaseModel):
    url: str
    path: Optional[str] = None
    token: Optional[str] = None

@router.post("/scan-github")
def scan_github(request: GitHubScanRequest):
    owner, repo, branch = extract_repo_info(request.url)
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    
    # 1. Handle Path Discovery or Targeted Analysis
    path = request.path
    token = request.token
    if not path:
        # Discovery Phase
        all_paths = find_all_dockerfiles(owner, repo, token=token)
        if not all_paths:
            raise HTTPException(status_code=404, detail="No Dockerfile found in repository")
        
        # If multiple found and no path specified, return list for selection
        if len(all_paths) > 1:
            return {
                "multi_service": True,
                "paths": all_paths,
                "owner": owner,
                "repo": repo,
                "url": request.url
            }
        path = all_paths[0]

    # 2. Analyze the specific path
    content = get_file_content(owner, repo, path, token=token)
    if not content:
        raise HTTPException(status_code=404, detail=f"Failed to fetch Dockerfile at {path}")
    
    # Use the unified static report builder (includes Trivy + AI)
    report = build_static_report(content)
    
    # Add GitHub metadata to the report
    report.update({
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "path": path,
        "original_content": content,
        "url": request.url,
        "multi_service": False
    })
    
    # Ensure ResultViewer can find the AI result
    if "recommendation" in report:
        rec = report["recommendation"]
        report["optimization"] = rec.get("optimized_dockerfile") or rec.get("dockerfile")
    
    return report

class CreateBulkPRRequest(BaseModel):
    url: str
    updates: list[dict] # list of {"path": str, "content": str}
    branch_name: Optional[str] = "optimize-all-services"
    base_branch: Optional[str] = None
    pr_title: Optional[str] = None
    commit_message: Optional[str] = None
    token: Optional[str] = None

@router.post("/create-bulk-pr")
def create_bulk_pr(request: CreateBulkPRRequest):
    owner, repo, branch = extract_repo_info(request.url)
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    
    try:
        pr_link = full_bulk_pr_workflow(
            owner=owner,
            repo=repo,
            updates=request.updates,
            branch_name=request.branch_name,
            base_branch=request.base_branch,
            pr_title=request.pr_title,
            commit_message=request.commit_message,
            token=request.token
        )
        return {"message": f"Successfully created PR: {pr_link}" if "github.com" in pr_link else pr_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RegistryScanRequest(BaseModel):
    image: str

@router.post("/scan-registry")
def scan_registry(request: RegistryScanRequest):
    return scan_registry_image(request.image)
