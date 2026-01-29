from .base import BaseOptimizer

class FallbackOptimizer(BaseOptimizer):
    def generate(self):
        return f"""
FROM alpine:3.21
WORKDIR /app
COPY . .
{self.common_hardening()}
CMD ["sh"]
"""
