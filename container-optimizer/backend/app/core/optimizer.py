import tempfile
import subprocess
import os
import docker

client = docker.from_env()

def detect_runtime(image_name: str) -> str:
    img = client.images.get(image_name)
    history = img.history()

    for layer in history:
        cmd = layer.get("CreatedBy", "").lower()
        if "python" in cmd:
            return "python"
        if "node" in cmd:
            return "node"
        if "java" in cmd:
            return "java"
        if "go" in cmd:
            return "go"

    return "unknown"


def generate_dockerfile(runtime: str) -> str:
    if runtime == "python":
        return """
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN useradd -m appuser
USER appuser

CMD ["python3", "app.py"]
""".strip()

    # fallback generic
    return """
FROM alpine:3.19
CMD ["sh"]
""".strip()


def build_optimized_image(image_name: str):
    runtime = detect_runtime(image_name)
    dockerfile = generate_dockerfile(runtime)

    optimized_image = f"{image_name.split(':')[0]}:optimized"

    with tempfile.TemporaryDirectory() as tmp:
        dockerfile_path = os.path.join(tmp, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile)

        subprocess.run(
            ["docker", "build", "-t", optimized_image, tmp],
            check=True
        )

    before = client.images.get(image_name)
    after = client.images.get(optimized_image)

    return {
        "runtime": runtime,
        "before": {
            "image": image_name,
            "size_mb": round(before.attrs["Size"] / (1024 * 1024), 2),
            "layers": len(before.history())
        },
        "after": {
            "image": optimized_image,
            "size_mb": round(after.attrs["Size"] / (1024 * 1024), 2),
            "layers": len(after.history())
        }
    }
