# Multi-stage build for Next.js frontend
FROM node:20-alpine as base

# Install dependencies only when needed
FROM base as deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --only=production --legacy-peer-deps; fi && npm cache clean --force

# Development stage
FROM base as development
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install --legacy-peer-deps; fi
COPY frontend/ .
CMD ["npm", "run", "dev"]

# Build stage
FROM base as builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

# Set environment for build
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build the application
RUN npm run build

# Production stage
FROM base as production
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]