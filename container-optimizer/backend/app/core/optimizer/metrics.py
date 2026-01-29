import subprocess


def image_metrics(image_ref: str):
    size = subprocess.check_output(
        ["docker", "image", "inspect", image_ref, "--format", "{{.Size}}"]
    ).decode().strip()

    size_mb = round(int(size) / (1024 * 1024), 2)

    layers = subprocess.check_output(
        ["docker", "history", image_ref, "--quiet"]
    ).decode().strip().splitlines()

    return {
        "size_mb": size_mb,
        "layer_count": len(layers)
    }
