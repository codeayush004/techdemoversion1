import subprocess
import tempfile
import json


def scan_image(image_name: str):
    """
    Run Trivy image scan safely.
    Returns parsed JSON or raises a controlled error.
    """
    with tempfile.TemporaryDirectory() as tmp:
        output_file = f"{tmp}/result.json"

        cmd = [
            "trivy",
            "image",
            "--scanners",
            "vuln,secret,misconfig",
            "--format",
            "json",
            "--output",
            output_file,
            image_name,
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "Trivy scan failed. Ensure Docker API compatibility and permissions."
            )

        with open(output_file) as f:
            return json.load(f)
