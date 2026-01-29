def analyze_misconfig(image_analysis: dict, runtime_analysis: dict):
    """
    Detect Docker image misconfigurations and bad practices.
    Reference: CIS Docker Benchmark, Docker Best Practices.
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
    if any(x in base_image.lower() for x in ["ubuntu", "debian", "fedora", "centos"]) and "slim" not in base_image.lower():
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
        if any(pkg in cmd for pkg in ["gcc", "build-essential", "make", "git", "curl"]):
            # Ignore curl if it's the only one, might be for healthcheck
            if "curl" in cmd and not any(pkg in cmd for pkg in ["gcc", "make", "git"]):
                continue
            issues.append({
                "id": "BUILD_TOOLS_PRESENT",
                "severity": "HIGH",
                "message": "Build tools or dev utilities present in final image",
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

    # 6. Missing HEALTHCHECK (New)
    has_healthcheck = any(
        "healthcheck" in (l.get("command") or "").lower()
        for l in image_analysis.get("layers", [])
    )
    if not has_healthcheck:
        issues.append({
            "id": "MISSING_HEALTHCHECK",
            "severity": "LOW",
            "message": "No HEALTHCHECK instruction found",
            "recommendation": "Add a HEALTHCHECK to monitor container liveness."
        })

    # 7. Shell form in CMD/ENTRYPOINT (New)
    for layer in image_analysis.get("layers", []):
        cmd = (layer.get("command") or "").lower()
        if ("/bin/sh -c" in cmd) and ("cmd [" not in cmd and "entrypoint [" not in cmd) and ("#(nop) cmd" in cmd or "#(nop) entrypoint" in cmd):
             issues.append({
                "id": "SHELL_FORM_COMMAND",
                "severity": "MEDIUM",
                "message": "CMD or ENTRYPOINT uses shell form",
                "recommendation": "Use the JSON form ['executable', 'param1', 'param2'] to avoid shell overhead and correctly handle signals."
            })
             break

    # 8. Version pinning (New)
    if "latest" in base_image.lower() or ":" not in base_image:
        issues.append({
            "id": "NO_VERSION_PINNING",
            "severity": "MEDIUM",
            "message": "Base image version not pinned (using 'latest')",
            "recommendation": "Pin specific version tags for reproducible builds."
        })

    return issues
