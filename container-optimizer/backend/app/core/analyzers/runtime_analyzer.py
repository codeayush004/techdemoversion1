from app.docker.client import get_docker_client
import docker

def analyze_runtime(image_ref: str, container_id: str = None):
    client = get_docker_client()

    # 1. Image Metadata Analysis
    try:
        image = client.images.get(image_ref)
    except docker.errors.ImageNotFound:
        # fallback: try without tag
        image = client.images.get(image_ref.split(":")[0])

    cfg = image.attrs.get("Config", {})
    user = cfg.get("User", "root")
    runs_as_root = user in ["", "0", "root"]

    # 2. Container Instance Analysis (Deep Inspection)
    instance_info = {}
    if container_id:
        try:
            container = client.containers.get(container_id)
            attrs = container.attrs
            host_config = attrs.get("HostConfig", {})
            config = attrs.get("Config", {})
            
            instance_info = {
                "id": container_id,
                "privileged": host_config.get("Privileged", False),
                "network_mode": host_config.get("NetworkMode", "default"),
                "memory_limit": host_config.get("Memory", 0),
                "cpu_shares": host_config.get("CpuShares", 0),
                "cap_add": host_config.get("CapAdd") or [],
                "mounts": attrs.get("Mounts") or [],
                "env": config.get("Env") or []
            }
        except Exception as e:
            print(f"Error inspecting container instance: {e}")

    return {
        "user": user,
        "runs_as_root": runs_as_root,
        "instance": instance_info
    }
