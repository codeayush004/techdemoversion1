def analyze_misconfig(image_analysis: dict, runtime_analysis: dict):
    """
    Detect Docker image misconfigurations and bad practices.
    """
    issues = []

    # 1. Root user
    if runtime_analysis.get("runs_as_root"):
        issues.append({
            "id": "RUNS_AS_ROOT",
            "severity": "HIGH",
            "message": "Container runs as root user",
            "recommendation": "Add a non-root USER in the Dockerfile."
        })

    # 2. Large base image
    base_image = image_analysis.get("base_image", "")
    if "ubuntu" in base_image or "debian" in base_image:
        issues.append({
            "id": "HEAVY_BASE_IMAGE",
            "severity": "MEDIUM",
            "message": f"Heavy base image detected ({base_image})",
            "recommendation": "Use slim or alpine base images where possible."
        })

    # 3. Large layers → likely no multi-stage
    large_layers = [
        l for l in image_analysis.get("layers", [])
        if l.get("is_large")
    ]

    if large_layers:
        issues.append({
            "id": "NO_MULTI_STAGE",
            "severity": "HIGH",
            "message": "Large build layers detected in final image",
            "recommendation": "Use multi-stage builds to exclude build dependencies."
        })

    # 4. Build tools in final image
    for layer in image_analysis.get("layers", []):
        cmd = (layer.get("command") or "").lower()
        if any(pkg in cmd for pkg in ["gcc", "build-essential", "make"]):
            issues.append({
                "id": "BUILD_TOOLS_PRESENT",
                "severity": "HIGH",
                "message": "Build tools present in final image",
                "recommendation": "Install build tools only in builder stage."
            })
            break

    # 5. COPY . /
    for layer in image_analysis.get("layers", []):
        if "copy . " in (layer.get("command") or "").lower():
            issues.append({
                "id": "COPY_ALL",
                "severity": "MEDIUM",
                "message": "COPY . / used (large build context)",
                "recommendation": "Use .dockerignore and copy only required files."
            })
            break

    return issues
