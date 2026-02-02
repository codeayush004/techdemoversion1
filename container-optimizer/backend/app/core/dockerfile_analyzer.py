import re

def analyze_dockerfile_content(content: str):
    """
    Statically analyze Dockerfile content with support for line continuations and multi-stage builds.
    """
    raw_lines = content.splitlines()
    processed_lines = []
    current_line = ""

    # 1. Handle line continuations (\)
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove inline comments but keep space for separator
        if "#" in line:
            line = line.split("#")[0].strip()
            if not line: continue

        if line.endswith("\\"):
            current_line += line[:-1].strip() + " "
        else:
            current_line += line
            processed_lines.append(current_line.strip())
            current_line = ""

    instructions = []
    stages = []
    
    for line in processed_lines:
        match = re.match(r"^([A-Z]+)\s+(.*)$", line, re.IGNORECASE)
        if match:
            instr = match.group(1).upper()
            value = match.group(2)
            instructions.append({"instruction": instr, "value": value})
            
            if instr == "FROM":
                # Handle 'FROM image AS stage'
                parts = value.split()
                base = parts[0]
                stage_name = None
                if "as" in [p.lower() for p in parts]:
                    idx = [p.lower() for p in parts].index("as")
                    if len(parts) > idx + 1:
                        stage_name = parts[idx + 1]
                stages.append({"base": base, "name": stage_name})

    # Prepare "layers" format for compatibility with misconfig_analyzer
    layers = []
    for inst in instructions:
        layers.append({
            "command": f"{inst['instruction']} {inst['value']}",
            "size_mb": 0.0,
            "is_large": False
        })

    # Final stage base image
    base_image = stages[-1]["base"] if stages else "unknown"
            
    # Detect user (check all stages but prioritize later instructions)
    user = "root"
    runs_as_root = True
    for inst in reversed(instructions):
        if inst["instruction"] == "USER":
            user = inst["value"]
            runs_as_root = user.lower() in ["root", "0", ""]
            break

    runtime = detect_runtime_from_content(content, instructions)

    return {
        "is_static": True,
        "base_image": base_image,
        "stages": stages,
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

    # 5. Rust
    if any(x in content_lower for x in ["cargo", "rustc", "cargo.toml", "cargo.lock"]):
        return "rust"

    # 6. Ruby
    if any(x in content_lower for x in ["ruby", "gem ", "bundle ", "gemfile"]):
        return "ruby"

    return "unknown"
