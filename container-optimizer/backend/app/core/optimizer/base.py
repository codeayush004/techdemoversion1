class BaseOptimizer:
    def common_hardening(self) -> str:
        return """
# Security hardening
RUN addgroup -S app && adduser -S app -G app
USER app
"""

    def dockerignore(self) -> str:
        return """
.git
.env
*.log
node_modules
__pycache__
"""
