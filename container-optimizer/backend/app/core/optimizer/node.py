from .base import BaseOptimizer

class NodeOptimizer(BaseOptimizer):
    def generate(self):
        return f"""
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app /app
{self.common_hardening()}
CMD ["node", "index.js"]
"""
