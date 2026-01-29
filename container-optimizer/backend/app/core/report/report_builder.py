from app.core.image_analyzer import analyze_image
from app.core.analyzers.runtime_analyzer import analyze_runtime
from app.core.analyzers.security_analyzer import analyze_security
from app.core.analyzers.misconfig_analyzer import analyze_misconfig
from app.core.suggestors.dockerfile_suggestor import suggest_dockerfile


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
