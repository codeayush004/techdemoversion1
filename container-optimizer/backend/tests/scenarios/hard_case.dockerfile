FROM ubuntu:20.04 AS builder
RUN apt-get update && apt-get install -y \
    curl \
    git # inline comment
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs
COPY . /app
WORKDIR /app
RUN npm install && \
    npm run build

FROM ubuntu:20.04
VOLUME ["/var/run/docker.sock"]
COPY --from=builder /app/dist /dist
CMD ["/dist/start.sh"]
