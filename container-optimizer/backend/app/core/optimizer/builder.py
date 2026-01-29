import os
import subprocess
import uuid


def build_image(dockerfile: str, context_path: str):
    image_tag = f"optimized:{uuid.uuid4().hex[:8]}"

    dockerfile_path = os.path.join(context_path, "Dockerfile")
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile)

    subprocess.run(
        ["docker", "build", "-t", image_tag, context_path],
        check=True
    )

    return image_tag
