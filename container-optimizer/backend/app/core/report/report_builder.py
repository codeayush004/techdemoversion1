import re
from app.core.image_analyzer import analyze_image
from app.core.analyzers.runtime_analyzer import analyze_runtime
from app.core.analyzers.security_analyzer import analyze_security, analyze_dockerfile_security
from app.core.analyzers.misconfig_analyzer import analyze_misconfig
from app.core.suggestors.dockerfile_suggestor import suggest_dockerfile
from app.core.dockerfile_analyzer import analyze_dockerfile_content
from app.core.ai_service import optimize_with_ai


def build_report(image_name: str, dockerfile_content: str = None, container_id: str = None):
    image = analyze_image(image_name)
    runtime = analyze_runtime(image_name, container_id=container_id)
    security = analyze_security(image_name)
    misconfigs = analyze_misconfig(image, runtime)
    
    # NEW: If dockerfile is attached to a running container scan, 
    # we merge its static findings too!
    if dockerfile_content:
        static_analysis = analyze_dockerfile_content(dockerfile_content)
        static_misconfigs = analyze_misconfig(static_analysis, runtime)
        # Check for secrets statically in the pasted text
        static_secrets = _detect_static_secrets(dockerfile_content)
        
        # Merge them (the deductive loop later will clean up repeats)
        misconfigs.extend(static_misconfigs)
        misconfigs.extend(static_secrets)

    # Prepare context for AI
    image_context = {
        "image": image_name,
        "runtime": runtime.get("runtime", "unknown"),
        "misconfigurations": misconfigs,
        "summary": {
            "image_size_mb": image["total_size_mb"],
            "layer_count": image["layer_count"],
            "runs_as_root": runtime["runs_as_root"],
        }
    }
    
    # Use AI for optimization and reasoning
    try:
        recommendation = optimize_with_ai(image_context, dockerfile_content)
    except Exception:
        # Fallback to rule-based if AI fails
        dockerfile_suggestion = suggest_dockerfile(image, runtime, misconfigs)
        recommendation = {
            "optimized_dockerfile": dockerfile_suggestion,
            "explanation": ["AI Optimization was unavailable, showing rule-based suggestions."],
            "security_warnings": []
        }

    raw_findings = []
    # 1. Runtime Insights
    for m in misconfigs:
        raw_findings.append({
            "category": "ANALYSIS",
            "message": m["message"],
            "severity": m.get("severity", "MEDIUM"),
            "recommendation": m.get("recommendation", "")
        })
        
    # 2. AI Semantic Checks (Unified Recommendation Logic)
    for w in recommendation.get("security_warnings", []):
        if not any(w.lower() in f["message"].lower() or f["message"].lower() in w.lower() for f in raw_findings):
            # Map specific AI warnings to technical resolutions to avoid "See AI reasoning"
            rec = "Apply the suggested architecture in the optimized Dockerfile."
            if "root" in w.lower(): rec = "Add a non-root USER and set appropriate permissions."
            elif "stage" in w.lower(): rec = "Use multi-stage builds to reduce image footprint."
            elif "secret" in w.lower() or "token" in w.lower(): rec = "Use build secrets or environment variables instead of hardcoding."
            elif "tool" in w.lower() or "install" in w.lower(): rec = "Clean package manager caches (apt/apk cleanup) in the same layer."
            
            raw_findings.append({
                "category": "ANALYSIS",
                "message": w,
                "severity": "HIGH",
                "recommendation": rec
            })

    # Verified Security CVEs (Only if scan was successful)
    for v in security.get("vulnerabilities", []):
        if v.get("severity") in ["HIGH", "CRITICAL"]:
            msg = f"{v['title']} ({v['id']})"
            if not any(v.get('id', 'unknown') in f["message"] for f in raw_findings):
                raw_findings.append({
                    "category": "SECURITY",
                    "message": msg,
                    "severity": v["severity"],
                    "recommendation": v.get("resolution", "")
                })

    # Final Semantic Deduplicate
    unique_findings = []
    seen_concepts = set()
    
    # Mapping of keywords to "Semantic Concepts"
    concept_map = {
        "root": "ROOT_USER", 
        "user": "ROOT_USER",
        "secret": "SECRET", 
        "token": "SECRET", 
        "password": "SECRET",
        "healthcheck": "HEALTHCHECK",
        "stage": "MULTI_STAGE", 
        "footprint": "MULTI_STAGE", 
        "layer": "MULTI_STAGE",
        "pin": "VERSION_PIN", 
        "latest": "VERSION_PIN"
    }

    for f in raw_findings:
        msg = f["message"].lower()
        # Find which concept this finding belongs to
        finding_concept = None
        for kw, concept in concept_map.items():
            if kw in msg:
                finding_concept = concept
                break
        
        # If it's a known concept, only add if we haven't seen it
        if finding_concept:
            if finding_concept not in seen_concepts:
                unique_findings.append(f)
                seen_concepts.add(finding_concept)
        else:
            # For unique security CVEs or other findings, use exact match
            if msg not in seen_concepts:
                unique_findings.append(f)
                seen_concepts.add(msg)

    return {
        "id": container_id,
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
        "recommendation": recommendation,
        "findings": unique_findings,
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

    # Prepare context for AI
    image_context = {
        "image": "uploaded_dockerfile",
        "runtime": image_analysis.get("runtime", "unknown"),
        "misconfigurations": misconfigs,
        "summary": {
            "layer_count": len(image_analysis["layers"]),
            "runs_as_root": runtime["runs_as_root"],
        }
    }

    # Use AI for optimization and reasoning
    try:
        recommendation = optimize_with_ai(image_context, dockerfile_content)
    except Exception:
        dockerfile_suggestion = suggest_dockerfile(image_analysis, runtime, misconfigs)
        recommendation = {
            "optimized_dockerfile": dockerfile_suggestion,
            "explanation": ["AI Optimization was unavailable, showing rule-based suggestions."],
            "security_warnings": []
        }

    raw_findings = []
    
    # 1. Misconfigurations (Strict/Verified)
    for m in misconfigs:
        raw_findings.append({
            "category": "ANALYSIS",
            "message": m["message"],
            "severity": m.get("severity", "MEDIUM"),
            "recommendation": m.get("recommendation", "")
        })
        
    # 2. AI (Deep Semantic Analysis)
    for w in recommendation.get("security_warnings", []):
        # Fuzzy check: Don't add if a similar message already exists from static scan
        if not any(w.lower() in f["message"].lower() or f["message"].lower() in w.lower() for f in raw_findings):
            # Map specific AI warnings to technical resolutions
            rec = "Implemented in the optimized Dockerfile."
            if "root" in w.lower(): rec = "Add a non-root USER and set appropriate permissions."
            elif "stage" in w.lower(): rec = "Use multi-stage builds to reduce image footprint."
            elif "secret" in w.lower() or "token" in w.lower(): rec = "Use build secrets or environment variables instead of hardcoding."
            elif "tool" in w.lower() or "install" in w.lower(): rec = "Clean package manager caches (apt/apk cleanup) in the same layer."
            
            raw_findings.append({
                "category": "ANALYSIS",
                "message": w,
                "severity": "HIGH",
                "recommendation": rec
            })

    # 3. Security (High/Critical)
    for v in security.get("vulnerabilities", []):
        if v["severity"] in ["HIGH", "CRITICAL"]:
            msg = f"{v['title']} ({v['id']})"
            if not any(v['id'] in f["message"] for f in raw_findings):
                raw_findings.append({
                    "category": "SECURITY",
                    "message": msg,
                    "severity": v["severity"],
                    "recommendation": v.get("resolution", "")
                })
            
    # Final Semantic Deduplicate
    unique_findings = []
    seen_concepts = set()
    
    concept_map = {
        "root": "ROOT_USER", 
        "user": "ROOT_USER",
        "secret": "SECRET", 
        "token": "SECRET", 
        "password": "SECRET",
        "healthcheck": "HEALTHCHECK",
        "stage": "MULTI_STAGE", 
        "footprint": "MULTI_STAGE", 
        "layer": "MULTI_STAGE",
        "pin": "VERSION_PIN", 
        "latest": "VERSION_PIN"
    }

    for f in raw_findings:
        msg = f["message"].lower()
        finding_concept = None
        for kw, concept in concept_map.items():
            if kw in msg:
                finding_concept = concept
                break
        
        if finding_concept:
            if finding_concept not in seen_concepts:
                unique_findings.append(f)
                seen_concepts.add(finding_concept)
        else:
            if msg not in seen_concepts:
                unique_findings.append(f)
                seen_concepts.add(msg)

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
        "recommendation": recommendation,
        "findings": unique_findings,
    }

def _detect_static_secrets(content: str):
    issues = []
    # Simplified patterns to reduce false positives
    secret_patterns = [
        (r"(?i)(aws_access_key_id|aws_secret_access_key|npm_token|github_token|secret_key|api_key|access_token|db_password)\s*[= ]\s*['\"]?\w{4,}", "Exposed Secret/Token"),
    ]
    
    lines = content.splitlines()
    for i, line in enumerate(lines):
        line_strip = line.strip()
        if re.search(r"^\s*(ENV|ARG)\s+", line_strip, re.IGNORECASE):
            for pattern, label in secret_patterns:
                if re.search(pattern, line_strip):
                    issues.append({
                        "id": "EXPOSED_SECRET",
                        "severity": "HIGH",
                        "message": f"Potential exposed secret ({label}) on line {i+1}",
                        "recommendation": "Use Docker Secrets or environment variables at runtime."
                    })
                    break
    return issues
