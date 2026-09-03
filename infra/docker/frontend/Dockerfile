# Frontend Next.js (doc 03)
FROM node:22-alpine

RUN corepack enable

WORKDIR /app

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./

EXPOSE 3000
CMD ["pnpm", "dev"]
