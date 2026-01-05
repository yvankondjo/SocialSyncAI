# ==============================================================================
# MULTI-STAGE DOCKERFILE FOR NEXT.JS FRONTEND
# Optimized for: Security (non-root), Performance (cache), Dev experience
# ==============================================================================

# ------------------------------------------------------------------------------
# STAGE 1: Dependencies - Install node_modules
# ------------------------------------------------------------------------------
FROM node:20-alpine AS deps

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package*.json ./

# Install dependencies with npm ci (faster & more reliable)
RUN if [ -f package-lock.json ] && [ -s package-lock.json ]; then \
        npm ci --legacy-peer-deps --no-audit --no-fund --prefer-offline; \
    else \
        npm install --legacy-peer-deps --no-audit --no-fund; \
    fi

# ------------------------------------------------------------------------------
# STAGE 2: Development - For hot reload
# ------------------------------------------------------------------------------
FROM node:20-alpine AS development

WORKDIR /app

# Install system dependencies and create non-root user
RUN apk add --no-cache libc6-compat wget && \
    addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs

# Copy dependencies from deps stage
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules

# Copy application code (will be overridden by volume in dev)
COPY --chown=nextjs:nodejs . .

# Create .next directory with proper ownership
RUN mkdir -p .next/cache .next/server && \
    chown -R nextjs:nodejs .next

# Switch to non-root user
USER nextjs

# Environment variables
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1
ENV WATCHPACK_POLLING=true
ENV PORT=3000

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Development command with hot reload
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]

# ------------------------------------------------------------------------------
# STAGE 3: Builder - Build Next.js for production
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache libc6-compat

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Build Next.js application
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ------------------------------------------------------------------------------
# STAGE 4: Production - Minimal runtime
# ------------------------------------------------------------------------------
FROM node:20-alpine AS production

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache libc6-compat wget && \
    addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs

# Copy necessary files from builder
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

# Production command
CMD ["node", "server.js"]
