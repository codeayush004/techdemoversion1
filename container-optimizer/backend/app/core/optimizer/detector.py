def detect_runtime(image_analysis: dict) -> str:
    layers = image_analysis.get("layers", [])
    base = image_analysis.get("base_image", "").lower()

    text = " ".join([l["command"].lower() for l in layers]) + base

    if "node" in text or "npm" in text or "yarn" in text:
        return "node"
    if "python" in text or "pip" in text:
        return "python"
    if "java" in text or "jdk" in text or "jre" in text:
        return "java"
    if "go" in text or "golang" in text:
        return "go"

    return "unknown"
