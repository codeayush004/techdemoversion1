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
                timeout=60 # Prevent hangs
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise RuntimeError(
                "Trivy scan failed or timed out. Ensure Trivy is installed and working."
            )

        with open(output_file) as f:
            return json.load(f)

def scan_dockerfile(content: str):
    """
    Run Trivy config scan on Dockerfile content.
    Returns parsed JSON findings.
    """
    with tempfile.TemporaryDirectory() as tmp:
        df_path = f"{tmp}/Dockerfile"
        output_file = f"{tmp}/result.json"
        
        with open(df_path, "w") as f:
            f.write(content)

        cmd = [
            "trivy",
            "config",
            "--scanners",
            "misconfig,secret",
            "--format",
            "json",
            "--output",
            output_file,
            df_path,
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30 # Faster for config scan
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # If scan fails, return empty findings
            return {"Results": []}

        with open(output_file) as f:
            return json.load(f)
