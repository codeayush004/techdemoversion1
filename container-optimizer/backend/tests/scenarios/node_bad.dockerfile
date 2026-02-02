FROM node:18
RUN apt-get update && apt-get install -y git make gcc
WORKDIR /usr/src/app
COPY package.json .
RUN npm install
COPY . .
EXPOSE 1024-65535
CMD "npm" "start"
