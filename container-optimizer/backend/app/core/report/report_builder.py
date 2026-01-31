import re
from app.core.image_analyzer import analyze_image
from app.core.analyzers.runtime_analyzer import analyze_runtime
from app.core.analyzers.security_analyzer import analyze_security, analyze_dockerfile_security
from app.core.analyzers.misconfig_analyzer import analyze_misconfig
from app.core.suggestors.dockerfile_suggestor import suggest_dockerfile
from app.core.dockerfile_analyzer import analyze_dockerfile_content


def build_report(image_name: str):
    image = analyze_image(image_name)
    runtime = analyze_runtime(image_name)
    security = analyze_security(image_name)
    misconfigs = analyze_misconfig(image, runtime)

    dockerfile_suggestion = suggest_dockerfile(
        image, runtime, misconfigs
    )

    findings = [m["message"] for m in misconfigs]

    if security["status"] == "error":
        findings.append("Security scan failed (environment or permission issue)")

    return {
        "image": image_name,
        "summary": {
            "image_size_mb": image["total_size_mb"],
            "layer_count": image["layer_count"],
            "runs_as_root": runtime["runs_as_root"],
            "security_scan_status": security["status"],
            "misconfiguration_count": len(misconfigs),
        },
        "image_analysis": image,
        "runtime_analysis": runtime,
        "security_analysis": security,
        "misconfigurations": misconfigs,
        "recommendation": {
            "dockerfile": dockerfile_suggestion
        },
        "findings": findings,
    }

def build_static_report(dockerfile_content: str):
    image_analysis = analyze_dockerfile_content(dockerfile_content)
    runtime = image_analysis["runtime_analysis"]
    
    # Run static security scan (Trivy config scan)
    security = analyze_dockerfile_security(dockerfile_content)
    
    misconfigs = analyze_misconfig(image_analysis, runtime)
    
    # Check for secrets in ENV/ARG statically (simple regex fallback)
    secrets = _detect_static_secrets(dockerfile_content)
    # Filter out duplicates if Trivy already caught them
    existing_messages = [m["message"] for m in misconfigs]
    for s in secrets:
        if s["message"] not in existing_messages:
            misconfigs.append(s)

    dockerfile_suggestion = suggest_dockerfile(
        image_analysis, runtime, misconfigs
    )

    findings = [m["message"] for m in misconfigs]
    for v in security.get("vulnerabilities", []):
        findings.append(f"Security Alert: {v['title']} ({v['severity']})")

    return {
        "image": "uploaded_dockerfile",
        "is_static": True,
        "summary": {
            "image_size_mb": 0,
            "layer_count": len(image_analysis["layers"]),
            "runs_as_root": runtime["runs_as_root"],
            "security_scan_status": security["status"],
            "misconfiguration_count": len(misconfigs),
        },
        "image_analysis": image_analysis,
        "runtime_analysis": runtime,
        "security_analysis": security,
        "misconfigurations": misconfigs,
        "recommendation": {
            "dockerfile": dockerfile_suggestion
        },
        "findings": findings,
    }

def _detect_static_secrets(content: str):
    issues = []
    # Broaden patterns for common secret keys and tokens
    secret_patterns = [
        (r"(?i)(aws_access_key_id|aws_secret_access_key|npm_token|secret_key|api_key|access_token|db_password)\s*[= ]\s*", "Sensitive Token/Key"),
    ]
    
    lines = content.splitlines()
    for i, line in enumerate(lines):
        # Look for ENV or ARG instructions explicitly if they contain sensitive variable names
        if re.search(r"^\s*(ENV|ARG)\s+", line.strip(), re.IGNORECASE):
            for pattern, label in secret_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "id": "EXPOSED_SECRET",
                        "severity": "HIGH",
                        "message": f"Potential exposed secret ({label}) on line {i+1}",
                        "recommendation": "Use Docker Secrets or environment variables at runtime, never hardcode them in the Dockerfile."
                    })
                    break # Only one issue per line for secrets
    return issues
