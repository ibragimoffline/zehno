# syntax=docker/dockerfile:1

########################################
# Base
########################################
FROM node:22-alpine AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json* ./
RUN npm install

########################################
# Development (hot reload)
########################################
FROM base AS development
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

########################################
# Builder
########################################
FROM base AS builder
COPY . .
RUN npm run build

########################################
# Production
########################################
FROM node:22-alpine AS production
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs
EXPOSE 3000
CMD ["npm", "run", "start"]
