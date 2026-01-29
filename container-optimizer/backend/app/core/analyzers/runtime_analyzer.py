from app.docker.client import get_docker_client
import docker

def analyze_runtime(image_ref: str):
    client = get_docker_client()

    try:
        image = client.images.get(image_ref)
    except docker.errors.ImageNotFound:
        # fallback: try without tag
        image = client.images.get(image_ref.split(":")[0])

    user = "root"
    runs_as_root = True

    cfg = image.attrs.get("Config", {})
    if cfg and cfg.get("User"):
        user = cfg["User"]
        runs_as_root = user in ["", "0", "root"]

    issues = []
    if runs_as_root:
        issues.append("Container runs as root user")

    return {
        "user": user,
        "runs_as_root": runs_as_root,
        "issues": issues
    }
