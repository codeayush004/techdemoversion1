from .base import BaseOptimizer

class JavaOptimizer(BaseOptimizer):
    def generate(self):
        return f"""
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
{self.common_hardening()}
CMD ["java", "-jar", "app.jar"]
"""
