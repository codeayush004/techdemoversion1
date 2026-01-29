def suggest_dockerfile(image_analysis, runtime_analysis, misconfigs):
    """
    Generate a safe, best-practice Dockerfile suggestion.
    """
    uses_python = any(
        "python" in (l.get("command") or "").lower()
        for l in image_analysis.get("layers", [])
    )

    suggestions = []
    explanation = []

    if uses_python:
        base = "python:3.11-slim"
        suggestions.append("FROM python:3.11-slim AS runtime")
        explanation.append("Slim Python base reduces image size and CVE surface.")
    else:
        base = "alpine:3.19"
        suggestions.append("FROM alpine:3.19 AS runtime")
        explanation.append("Alpine base reduces image size.")

    suggestions += [
        "",
        "WORKDIR /app",
        "",
        "# Copy only required application files",
        "COPY . /app",
        "",
        "# Create non-root user",
        "RUN useradd -m appuser",
        "USER appuser",
        "",
        'CMD ["python3", "app.py"]' if uses_python else 'CMD ["sh"]',
    ]

    return {
        "type": "suggested",
        "base_image": base,
        "dockerfile": "\n".join(suggestions),
        "explanation": explanation,
        "disclaimer": (
            "This Dockerfile is a suggestion generated from image analysis. "
            "Review and adjust before using in production."
        ),
    }
