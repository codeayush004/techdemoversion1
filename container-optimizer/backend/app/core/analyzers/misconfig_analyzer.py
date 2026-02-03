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

    # 10. Runtime Instance Checks
    inst = runtime_analysis.get("instance", {})
    if inst:
        # Privileged mode
        if inst.get("privileged"):
            issues.append({
                "id": "RUNTIME_PRIVILEGED",
                "severity": "CRITICAL",
                "message": "Container is running in PRIVILEGED mode",
                "recommendation": "Disable privileged mode and use specific cap-add/cap-drop instead."
            })
        
        # Host network
        if inst.get("network_mode") == "host":
            issues.append({
                "id": "RUNTIME_HOST_NETWORK",
                "severity": "HIGH",
                "message": "Container is sharing the HOST network namespace",
                "recommendation": "Use bridge network or custom overlay networks for isolation."
            })

        # Resource Limits
        if inst.get("memory_limit") == 0:
            issues.append({
                "id": "RUNTIME_NO_MEMORY_LIMIT",
                "severity": "MEDIUM",
                "message": "No memory limit set for active container",
                "recommendation": "Set --memory limit to prevent OOM on host."
            })
        
        # Volume Inefficiencies & Sensitive Mounts
        mounts = inst.get("mounts", [])
        
        # 1. Anonymous volumes check
        anonymous_volumes = [m for m in mounts if not m.get("Name") and m.get("Type") == "volume"]
        if anonymous_volumes:
            issues.append({
                "id": "RUNTIME_ANONYMOUS_VOLUMES",
                "severity": "LOW",
                "message": f"Detected {len(anonymous_volumes)} anonymous/unused volumes",
                "recommendation": "Use named volumes or bind mounts for persistent data."
            })

        # 2. Sensitive Bind Mounts check
        sensitive_paths = ["/etc", "/proc", "/sys", "/var/run/docker.sock", "/dev", "/root", "/"]
        for m in mounts:
            source = m.get("Source", "")
            is_rw = m.get("RW", False)
            
            if any(source.startswith(p) for p in sensitive_paths):
                # Specific check for docker.sock vs files
                risk_label = "SENSITIVE HOST DIRECTORY"
                if "docker.sock" in source:
                    risk_label = "DOCKER SOCKET"
                
                issues.append({
                    "id": "RUNTIME_SENSITIVE_MOUNT",
                    "severity": "CRITICAL" if is_rw else "HIGH",
                    "message": f"Exposure of {risk_label} ({source}) detected",
                    "recommendation": f"Remove bind mount for {source}. Re-architect to avoid host level access."
                })

    return issues
