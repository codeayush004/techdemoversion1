FROM maven:3.8-openjdk-11
WORKDIR /app
COPY . .
RUN mvn package
ENV AWS_SECRET_ACCESS_KEY="my-secret-key"
CMD java -jar target/app.jar
