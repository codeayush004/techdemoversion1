import re

def analyze_dockerfile_content(content: str):
    """
    Statically analyze Dockerfile content without building an image.
    Returns an analysis object compatible with misconfig_analyzer and suggestor.
    """
    lines = content.splitlines()
    instructions = []
    
    # Simple regex to extract instructions
    # This is a basic parser; for production, we might use a formal dockerfile parser
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        match = re.match(r"^([A-Z]+)\s+(.*)$", line, re.IGNORECASE)
        if match:
            instr = match.group(1).upper()
            value = match.group(2)
            instructions.append({"instruction": instr, "value": value})

    # Prepare "layers" format for compatibility with misconfig_analyzer
    layers = []
    for inst in instructions:
        layers.append({
            "command": f"{inst['instruction']} {inst['value']}",
            "size_mb": 0.0,
            "is_large": False
        })

    # Detect base image
    base_image = "unknown"
    for inst in instructions:
        if inst["instruction"] == "FROM":
            base_image = inst["value"].split()[0]
            
    # Detect user
    user = "root"
    runs_as_root = True
    for inst in reversed(instructions):
        if inst["instruction"] == "USER":
            user = inst["value"]
            runs_as_root = user.lower() in ["root", "0", ""]
            break

    # Detect runtime (re-use logic or similar)
    runtime = detect_runtime_from_content(content, instructions)

    # Return structure compatible with the rest of the app
    return {
        "is_static": True,
        "base_image": base_image,
        "layers": layers,
        "runtime": runtime,
        "runtime_analysis": {
            "user": user,
            "runs_as_root": runs_as_root,
            "issues": ["Container runs as root user"] if runs_as_root else []
        }
    }

def detect_runtime_from_content(content: str, instructions: list):
    content_lower = content.lower()
    
    # 1. Python
    if any(x in content_lower for x in ["python", "pip", "requirements.txt", "poetry.lock"]):
        return "python"
    
    # 2. Node.js
    if any(x in content_lower for x in ["node", "npm", "yarn", "package.json", "package-lock.json"]):
        return "node"
    
    # 3. Go
    if any(x in content_lower for x in ["go build", "go.mod", "go.sum"]):
        return "go"
    
    # 4. Java
    if any(x in content_lower for x in ["java -jar", "javac", "mvn ", "gradle ", "pom.xml", "build.gradle"]):
        return "java"

    return "unknown"
