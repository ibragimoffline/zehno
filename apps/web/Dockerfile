# syntax=docker/dockerfile:1

########################################
# Base
########################################
FROM node:22-alpine AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

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
# Production — Next.js standalone chiqishi
#   node_modules to'liq nusxalanmaydi: `output: "standalone"` faqat
#   haqiqatda ishlatiladigan modullarni server.js yoniga yig'adi.
########################################
FROM node:22-alpine AS production
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
