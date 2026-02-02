def analyze_misconfig(image_analysis: dict, runtime_analysis: dict):
    """
    Detect Docker image misconfigurations and bad practices.
    """
    issues = []
    layers = image_analysis.get("layers", [])

    def _get_clean_cmd(l):
        cmd = (l.get("command") or "").lower()
        return cmd.replace("#(nop)", "").strip()

    # 1. Root user
    if runtime_analysis.get("runs_as_root"):
        issues.append({
            "id": "RUN_AS_ROOT",
            "severity": "HIGH",
            "message": "Container runs as root user",
            "recommendation": "Add a non-root USER in the Dockerfile."
        })

    # 2. Heavy base image
    base_image = image_analysis.get("base_image", "")
    if any(x in base_image.lower() for x in ["ubuntu", "debian", "fedora", "centos"]) and "slim" not in base_image.lower():
        issues.append({
            "id": "HEAVY_BASE_IMAGE",
            "severity": "MEDIUM",
            "message": f"Heavy base image detected ({base_image})",
            "recommendation": "Use slim or alpine base images."
        })

    # 3. Multi-stage detection (static only check)
    if image_analysis.get("is_static"):
        stages = image_analysis.get("stages", [])
        if len(stages) < 2:
            issues.append({
                "id": "SINGLE_STAGE",
                "severity": "LOW",
                "message": "Single stage build detected",
                "recommendation": "Consider multi-stage builds to reduce image size."
            })

    # 4. Large layers (runtime only check)
    if not image_analysis.get("is_static"):
        large_layers = [l for l in layers if l.get("is_large")]
        if large_layers:
            issues.append({
                "id": "NO_MULTI_STAGE",
                "severity": "HIGH",
                "message": "Large build layers detected in final image",
                "recommendation": "Use multi-stage builds to exclude build tools."
            })

    # 5. Build tools & Docker socket EXTREME risk
    docker_socket_risk = False
    for layer in layers:
        cmd = _get_clean_cmd(layer)
        
        # Check for docker.sock mount in VOLUME or ENV
        if "/var/run/docker.sock" in cmd:
            docker_socket_risk = True
            
        if any(pkg in cmd for pkg in ["gcc", "build-essential", "make", "git"]) and not "curl" in cmd:
            issues.append({
                "id": "BUILD_TOOLS_PRESENT",
                "severity": "HIGH",
                "message": "Build tools present in final image",
                "recommendation": "Install build tools only in builder stage."
            })
            break

    if docker_socket_risk:
        issues.append({
            "id": "DOCKER_SOCKET_MOUNT",
            "severity": "HIGH",
            "message": "Exposure of /var/run/docker.sock detected",
            "recommendation": "NEVER mount the Docker socket inside a container. This is an extreme security risk."
        })

    # 6. COPY . /
    for layer in layers:
        cmd = _get_clean_cmd(layer)
        if "copy . " in cmd and "copy . . " not in cmd: # Basic check
            issues.append({
                "id": "COPY_ALL",
                "severity": "MEDIUM",
                "message": "COPY . / used (potential large context)",
                "recommendation": "Use .dockerignore and copy individual files."
            })
            break

    # 7. Missing HEALTHCHECK
    has_healthcheck = any("healthcheck" in _get_clean_cmd(l) for l in layers)
    if not has_healthcheck:
        issues.append({
            "id": "MISSING_HEALTHCHECK",
            "severity": "LOW",
            "message": "No HEALTHCHECK instruction found",
            "recommendation": "Add a HEALTHCHECK for liveness monitoring."
        })

    # 8. Excessive EXPOSE range
    for layer in layers:
        cmd = _get_clean_cmd(layer)
        if "expose" in cmd:
            if "-" in cmd:
                parts = cmd.split()
                for p in parts:
                    if "-" in p:
                        try:
                            start, end = map(int, p.split("-"))
                            if end - start > 100:
                                issues.append({
                                    "id": "EXCESSIVE_EXPOSE",
                                    "severity": "MEDIUM",
                                    "message": f"Excessive port range exposed: {p}",
                                    "recommendation": "Expose only the specific ports your application needs."
                                })
                        except ValueError: continue

    # 9. Version pinning
    if "latest" in base_image.lower() or ":" not in base_image:
        issues.append({
            "id": "NO_VERSION_PINNING",
            "severity": "MEDIUM",
            "message": "Base image version not pinned (using 'latest')",
            "recommendation": "Pin specific version tags for reproducible builds."
        })

    return issues
