import re
from app.core.image_analyzer import analyze_image
from app.core.analyzers.runtime_analyzer import analyze_runtime
from app.core.analyzers.security_analyzer import analyze_security, analyze_dockerfile_security
from app.core.analyzers.misconfig_analyzer import analyze_misconfig
from app.core.suggestors.dockerfile_suggestor import suggest_dockerfile
from app.core.dockerfile_analyzer import analyze_dockerfile_content
from app.core.ai_service import optimize_with_ai


def _extract_tag(message: str):
    """Extracts [TAG] from the beginning of a message."""
    match = re.search(r"\[([A-Z0-9_]+)\]", message)
    return match.group(1) if match else None

def _normalize(text: str):
    """Normalizes text for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', text.lower())


def build_report(image_name: str, dockerfile_content: str = None, container_id: str = None):
    image = analyze_image(image_name)
    runtime = analyze_runtime(image_name, container_id=container_id)
    security = analyze_security(image_name)
    misconfigs = analyze_misconfig(image, runtime)

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
    # 1. Runtime Insights (Rule Engine)
    for m in misconfigs:
        raw_findings.append({
            "id": m.get("id"),
            "category": "ANALYSIS",
            "message": m["message"],
            "severity": m.get("severity", "MEDIUM"),
            "recommendation": m.get("recommendation", ""),
            "source": "rules"
        })
        
    # 2. AI Semantic Checks (Deep Reasoning)
    for w in recommendation.get("security_warnings", []):
        ai_tag = _extract_tag(w)
        w_clean = re.sub(r"\[[A-Z0-9_]+\]", "", w).strip()
        
        # Check against already added findings (usually rule-based misconfigs)
        is_duplicate = False
        for f in raw_findings:
            f_id = f.get("id")
            # 1. Match by Tag/ID
            if ai_tag and f_id and ai_tag == f_id:
                is_duplicate = True
                # Enhance existing finding with AI flavor if needed
                f["source"] = "hybrid" # Mark as corroborated by AI
                break
            
            # 2. Fuzzy match by content
            f_norm = _normalize(f["message"])
            w_norm = _normalize(w_clean)
            if w_norm in f_norm or f_norm in w_norm:
                is_duplicate = True
                f["source"] = "hybrid"
                break
        
        if not is_duplicate:
            # Map specific AI warnings to technical resolutions to avoid "See AI reasoning"
            rec = "Apply the suggested architecture in the optimized Dockerfile."
            w_low = w_clean.lower()
            if "root" in w_low: rec = "Add a non-root USER and set appropriate permissions."
            elif "stage" in w_low: rec = "Use multi-stage builds to reduce image footprint."
            elif "secret" in w_low or "token" in w_low: rec = "Use build secrets or environment variables instead of hardcoding."
            elif "tool" in w_low or "install" in w_low: rec = "Clean package manager caches (apt/apk cleanup) in the same layer."
            
            raw_findings.append({
                "id": ai_tag,
                "category": "ANALYSIS",
                "message": w_clean,
                "severity": "HIGH",
                "recommendation": rec,
                "source": "ai"
            })

    # Verified Security CVEs (Only if scan was successful)
    for v in security.get("vulnerabilities", []):
        if v.get("severity") in ["HIGH", "CRITICAL"]:
            v_id = v.get('id', 'unknown')
            msg = f"{v['title']} ({v_id})"
            
            is_seen = False
            for f in raw_findings:
                if v_id in f["message"]:
                    is_seen = True
                    break
            
            if not is_seen:
                raw_findings.append({
                    "id": v_id,
                    "category": "SECURITY",
                    "message": msg,
                    "severity": v["severity"],
                    "recommendation": v.get("resolution", ""),
                    "source": "security_scanner"
                })

    # Final Deduplicate
    unique_findings = []
    seen = set()
    for f in raw_findings:
        if f["message"].lower().strip() not in seen:
            unique_findings.append(f)
            seen.add(f["message"].lower().strip())

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
    
    # 1. Misconfigurations (Rules Engine)
    for m in misconfigs:
        raw_findings.append({
            "id": m.get("id"),
            "category": "ANALYSIS",
            "message": m["message"],
            "severity": m.get("severity", "MEDIUM"),
            "recommendation": m.get("recommendation", ""),
            "source": "rules"
        })
        
    # 2. AI (Deep Semantic Analysis)
    for w in recommendation.get("security_warnings", []):
        ai_tag = _extract_tag(w)
        w_clean = re.sub(r"\[[A-Z0-9_]+\]", "", w).strip()

        is_duplicate = False
        for f in raw_findings:
            f_id = f.get("id")
            # 1. Match by Tag/ID
            if ai_tag and f_id and ai_tag == f_id:
                is_duplicate = True
                f["source"] = "hybrid"
                break
            
            # 2. Fuzzy match
            f_norm = _normalize(f["message"])
            w_norm = _normalize(w_clean)
            if w_norm in f_norm or f_norm in w_norm:
                is_duplicate = True
                f["source"] = "hybrid"
                break
            
        if not is_duplicate:
            # Map specific AI warnings to technical resolutions
            rec = "Implemented in the optimized Dockerfile."
            w_low = w_clean.lower()
            if "root" in w_low: rec = "Add a non-root USER and set appropriate permissions."
            elif "stage" in w_low: rec = "Use multi-stage builds to reduce image footprint."
            elif "secret" in w_low or "token" in w_low: rec = "Use build secrets or environment variables instead of hardcoding."
            elif "tool" in w_low or "install" in w_low: rec = "Clean package manager caches (apt/apk cleanup) in the same layer."
            
            raw_findings.append({
                "id": ai_tag,
                "category": "ANALYSIS",
                "message": w_clean,
                "severity": "HIGH",
                "recommendation": rec,
                "source": "ai"
            })

    # 3. Security (High/Critical)
    for v in security.get("vulnerabilities", []):
        if v["severity"] in ["HIGH", "CRITICAL"]:
            v_id = v.get('id', 'unknown')
            msg = f"{v['title']} ({v_id})"

            if not any(v_id in f["message"] for f in raw_findings):
                raw_findings.append({
                    "id": v_id,
                    "category": "SECURITY",
                    "message": msg,
                    "severity": v["severity"],
                    "recommendation": v.get("resolution", ""),
                    "source": "security_scanner"
                })
            
    # Final Deduplication & Cleanup
    unique_findings = []
    seen_msgs = set()
    for f in raw_findings:
        msg_norm = f["message"].lower().strip()
        if msg_norm not in seen_msgs:
            unique_findings.append(f)
            seen_msgs.add(msg_norm)

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
