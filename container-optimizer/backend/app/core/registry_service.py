import docker
from app.docker.client import get_docker_client
from app.core.report.report_builder import build_report
from fastapi import HTTPException

def scan_registry_image(image_ref: str):
    client = get_docker_client()
    
    try:
        # 1. Pull the image from registry
        # This will follow normal Docker Hub / Registry logic
        print(f"Pulling image: {image_ref}...")
        try:
            client.images.pull(image_ref)
        except docker.errors.APIError as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=f"Image {image_ref} not found on Docker Hub")
            raise HTTPException(status_code=500, detail=f"Failed to pull image: {str(e)}")
        
        # 2. Run the unified report builder
        # Since the image is now local, build_report will work perfectly
        report = build_report(image_ref)
        
        # Mark it as a registry scan for frontend differentiation
        report["is_registry"] = True
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registry scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registry scan analysis failed: {str(e)}")
