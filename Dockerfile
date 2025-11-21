FROM node:18-slim

RUN apt update && apt install -y ffmpeg curl python3 python3-pip nodejs npm

RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp && chmod a+rx /usr/local/bin/yt-dlp

RUN yt-dlp --version

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 8080
CMD ["node", "server.js"]
