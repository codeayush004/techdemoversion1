from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.report.report_builder import build_report, build_static_report
from app.core.ai_service import optimize_with_ai
from app.docker.client import get_docker_client

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
