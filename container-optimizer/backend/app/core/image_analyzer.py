import subprocess
import docker
from app.docker.client import get_docker_client

LARGE_LAYER_THRESHOLD_MB = 50


def analyze_image(image_ref: str):
    """
    Analyze a LOCAL Docker image.
    No auto-pull. Industry-safe behavior.
    """
    client = get_docker_client()

    image = resolve_image(client, image_ref)

    image_size_mb = round(image.attrs["Size"] / (1024 * 1024), 2)
    image_id = image.id  # always safe

    result = subprocess.run(
        [
            "docker",
            "history",
            image_id,
            "--no-trunc",
            "--format",
            "{{.Size}}|{{.CreatedBy}}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    layers = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        size_str, command = line.split("|", 1)
        size_mb = parse_size(size_str)

        layers.append(
            {
                "command": command.strip(),
                "size_mb": size_mb,
                "is_large": size_mb >= LARGE_LAYER_THRESHOLD_MB,
            }
        )

    base_image = extract_base_image(layers)

    return {
        "image": image_ref,
        "total_size_mb": image_size_mb,
        "layer_count": len(layers),
        "base_image": base_image,
        "layers": layers,
    }


def resolve_image(client: docker.DockerClient, image_ref: str):
    """
    Resolve image strictly from local Docker daemon.
    """
    try:
        return client.images.get(image_ref)
    except docker.errors.ImageNotFound:
        raise RuntimeError(
            f"Image '{image_ref}' not found locally. "
            "Build or pull it before analysis."
        )


def parse_size(size_str: str) -> float:
    size_str = size_str.strip()

    if size_str == "0B":
        return 0.0
    if "kB" in size_str:
        return round(float(size_str.replace("kB", "")) / 1024, 2)
    if "MB" in size_str:
        return float(size_str.replace("MB", ""))
    if "GB" in size_str:
        return float(size_str.replace("GB", "")) * 1024

    return 0.0


def extract_base_image(layers):
    for layer in reversed(layers):
        if "FROM" in layer["command"]:
            return layer["command"].split("FROM")[-1].strip()
    return "unknown"
