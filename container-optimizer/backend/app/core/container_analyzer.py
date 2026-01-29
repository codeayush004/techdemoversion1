import psutil
from app.docker.client import get_docker_client

def get_running_containers():
    client = get_docker_client()
    containers = client.containers.list(all=True)

    results = []

    for c in containers:
        try:
            image = client.images.get(c.image.id)
            image_size_mb = round(image.attrs["Size"] / (1024 * 1024), 2)

            stats = c.stats(stream=False)
            mem_usage = stats["memory_stats"].get("usage", 0)
            memory_usage_mb = round(mem_usage / (1024 * 1024), 2)

            results.append({
                "id": c.short_id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "status": c.status,
                "image_size_mb": image_size_mb,
                "memory_usage_mb": memory_usage_mb
            })

        except Exception as e:
            print(f"Failed to inspect container {c.name}: {e}")

    return results
