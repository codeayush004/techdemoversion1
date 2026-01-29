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
    
    # New: Enhanced runtime detection
    runtime_info = detect_runtime(image, layers)

    return {
        "image": image_ref,
        "total_size_mb": image_size_mb,
        "layer_count": len(layers),
        "base_image": base_image,
        "layers": layers,
        "runtime": runtime_info,
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
        cmd = layer["command"]
        if "FROM" in cmd:
            return cmd.split("FROM")[-1].strip()
        # Common pattern: NOP instruction often indicates base image layers in older docker versions
        if "/bin/sh -c #(nop)" in cmd and "FROM" not in cmd:
            continue
    
    # Fallback: check first layer if it looks like a base image setup
    if layers:
        first_cmd = layers[-1]["command"].lower()
        if "bash" in first_cmd or "sh" in first_cmd or "add" in first_cmd:
             return "detected_via_history"

    return "unknown"


def detect_runtime(image, layers):
    """
    Detect the likely runtime (Python, Node, Go, Java) based on:
    1. Environment variables
    2. Commands in layers
    3. File system hits (if we were to explore, but here we stick to metadata)
    """
    config = image.attrs.get("Config", {})
    env = config.get("Env", [])
    env_str = " ".join(env).lower()
    
    all_cmds = " ".join([l["command"] for l in layers]).lower()
    
    # 1. Python
    if any(x in env_str for x in ["python", "pip", "poetry"]):
        return "python"
    if any(x in all_cmds for x in ["python", "pip", "requirements.txt"]):
        return "python"
    
    # 2. Node.js
    if any(x in env_str for x in ["node", "npm", "yarn"]):
        return "node"
    if any(x in all_cmds for x in ["node", "npm", "yarn", "package.json"]):
        return "node"
    
    # 3. Go
    if "go1." in env_str or "gopath" in env_str:
        return "go"
    if "go build" in all_cmds:
        return "go"
    
    # 4. Java
    if any(x in env_str for x in ["java", "jvm", "openjdk", "jdk", "maven", "gradle"]):
        return "java"
    if any(x in all_cmds for x in ["java -jar", "javac", "mvn ", "gradle "]):
        return "java"

    return "unknown"
