def suggest_dockerfile(image_analysis, runtime_analysis, misconfigs):
    """
    Generate a safe, best-practice Dockerfile suggestion based on runtime and detected issues.
    Supports Multi-stage builds, non-root users, and healthchecks.
    """
    runtime = image_analysis.get("runtime", "unknown")
    explanation = ["Applying industry best practices for container images."]
    
    if runtime == "python":
        dockerfile = _suggest_python()
        explanation += [
            "Using multi-stage build to separate build dependencies from the runtime environment.",
            "Utilizing python-slim as a base to reduce size and attack surface.",
            "Implementing a non-root 'appuser' for enhanced security.",
            "Added a basic HEALTHCHECK for liveness monitoring."
        ]
    elif runtime == "node":
        dockerfile = _suggest_node()
        explanation += [
            "Using multi-stage build to keep node_modules lean in the final image.",
            "Utilizing node:iron-slim (LTS) for stability and small footprint.",
            "Running as the built-in 'node' non-root user.",
            "Added HEALTHCHECK targeting the application port."
        ]
    elif runtime == "go":
        dockerfile = _suggest_go()
        explanation += [
            "Using multi-stage build: compiling in golang-alpine and running in a minimal alpine image.",
            "Final image contains only the compiled binary, drastically reducing size.",
            "Implementing a non-root 'appuser'.",
            "Added HEALTHCHECK for the service."
        ]
    elif runtime == "java":
        dockerfile = _suggest_java()
        explanation += [
            "Using multi-stage build to build with Maven and run on a lightweight JRE.",
            "Utilizing eclipse-temurin for a production-grade JRE environment.",
            "Implementing a non-root 'appuser'.",
            "Added HEALTHCHECK for the application."
        ]
    else:
        # Fallback to a hardened Generic Alpine template
        dockerfile = _suggest_generic()
        explanation += [
            "Falling back to a hardened Alpine base since runtime was not specifically identified.",
            "Implementing basic security hardening like non-root user and healthchecks."
        ]

    return {
        "type": "suggested",
        "runtime": runtime,
        "dockerfile": dockerfile,
        "explanation": explanation,
        "dockerignore": _get_dockerignore(runtime),
        "disclaimer": (
            "This Dockerfile is a best-practice template generated from image metadata. "
            "Please adjust the COPY paths, exposed ports, and HEALTHCHECK commands to match your specific application structure."
        ),
    }

def _get_dockerignore(runtime):
    common = [
        "**/.git",
        "**/.gitignore",
        "**/node_modules",
        "**/venv",
        "**/.venv",
        "**/.env",
        "**/dist",
        "**/build",
        "**.md",
        "Dockerfile*",
        ".dockerignore",
    ]
    if runtime == "python":
        common += ["**/__pycache__", "**/*.pyc", "**/*.pyo", "**/*.pyd", ".pytest_cache"]
    elif runtime == "node":
        common += ["npm-debug.log*", "yarn-debug.log*", "yarn-error.log*"]
    
    return "\n".join(common)

def _suggest_python():
    return """# Stage 1: Build
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
# Modern: Use cache mount for pip
RUN --mount=type=cache,target=/root/.cache/pip \\
    pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY . .

# Ensure scripts in .local/bin are in PATH
ENV PATH=/home/appuser/.local/bin:$PATH

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=3s \\
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "app.py"]
""".strip()

def _suggest_node():
    return """# Stage 1: Build
FROM node:20-slim AS builder

WORKDIR /app
COPY package*.json ./
# Modern: Use cache mount for npm
RUN --mount=type=cache,target=/root/.npm \\
    npm ci --only=production

# Stage 2: Runtime
FROM node:20-slim AS runtime

WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

# Use built-in node user
USER node

HEALTHCHECK --interval=30s --timeout=3s \\
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => { if (r.statusCode !== 200) process.exit(1); })"

CMD ["npm", "start"]
""".strip()

def _suggest_go():
    return """# Stage 1: Build
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .
RUN go build -o main .

# Stage 2: Runtime
FROM alpine:3.19 AS runtime

WORKDIR /app
COPY --from=builder /app/main .

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=3s \\
  CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["./main"]
""".strip()

def _suggest_java():
    return """# Stage 1: Build
FROM maven:3.9-eclipse-temurin-21 AS builder

WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM eclipse-temurin:21-jre-jammy AS runtime

WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=3s \\
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["java", "-jar", "app.jar"]
""".strip()

def _suggest_generic():
    return """FROM alpine:3.19

WORKDIR /app
COPY . .

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=3s \\
  CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["sh"]
""".strip()
