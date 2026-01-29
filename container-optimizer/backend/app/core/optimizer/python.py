from .base import BaseOptimizer

class PythonOptimizer(BaseOptimizer):
    def generate(self):
        return f"""
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app /app
{self.common_hardening()}
CMD ["python", "main.py"]
"""
