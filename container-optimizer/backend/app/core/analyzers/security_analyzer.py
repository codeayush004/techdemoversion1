from app.core.security_scanner import scan_image, scan_dockerfile


def analyze_security(image_name: str):
    try:
        scan = scan_image(image_name)
        vulnerabilities = scan.get("vulnerabilities", [])

        severity_count = {}
        for v in vulnerabilities:
            sev = v.get("severity", "UNKNOWN")
            severity_count[sev] = severity_count.get(sev, 0) + 1

        return {
            "status": "ok",
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": severity_count,
            "vulnerabilities": vulnerabilities,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "total_vulnerabilities": 0,
            "by_severity": {},
            "vulnerabilities": [],
        }

def analyze_dockerfile_security(content: str):
    """
    Analyzes security of a Dockerfile using Trivy config scan.
    Returns findings in a format consistent with analyze_security.
    """
    try:
        scan = scan_dockerfile(content)
        results = scan.get("Results", [])
        
        vulnerabilities = []
        severity_count = {}

        for result in results:
            # Trivy 'config' scan returns Misconfigurations and Secrets
            misconfigs = result.get("Misconfigurations", [])
            secrets = result.get("Secrets", [])
            
            for m in misconfigs + secrets:
                sev = m.get("Severity", "UNKNOWN")
                severity_count[sev] = severity_count.get(sev, 0) + 1
                
                vulnerabilities.append({
                    "id": m.get("ID") or m.get("RuleID"),
                    "title": m.get("Title") or m.get("Message"),
                    "severity": sev,
                    "description": m.get("Description", ""),
                    "resolution": m.get("Resolution", "")
                })

        return {
            "status": "ok",
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": severity_count,
            "vulnerabilities": vulnerabilities,
        }
    except Exception as e:
        print(f"Dockerfile Security Analysis Error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "total_vulnerabilities": 0,
            "by_severity": {},
            "vulnerabilities": [],
        }
