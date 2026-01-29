from .base import BaseOptimizer

class GoOptimizer(BaseOptimizer):
    def generate(self):
        return f"""
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o app

FROM gcr.io/distroless/base-debian12
WORKDIR /app
COPY --from=builder /app/app /app/app
USER nonroot
CMD ["/app/app"]
"""
