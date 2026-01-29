from app.core.security_scanner import scan_image


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
