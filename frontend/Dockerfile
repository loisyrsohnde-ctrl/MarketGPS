# ============================================================================
# MarketGPS Frontend Dockerfile
# Multi-stage build for Next.js production deployment
# ============================================================================

# --- build stage ---
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies for native modules
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables (defaults = production values)
ARG NEXT_PUBLIC_API_URL=https://api.marketgps.online
ARG NEXT_PUBLIC_API_BASE_URL=https://api.marketgps.online
ARG NEXT_PUBLIC_SUPABASE_URL=https://avecmzmcfliaeuxnwimu.supabase.co
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF2ZWNtem1jZmxpYWV1eG53aW11Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgwODU2NjQsImV4cCI6MjA4MzY2MTY2NH0.LjeknrD5c9Favt3SYi33yZgd023FBeSKBbvPUe6Yp90

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_TELEMETRY_DISABLED=1

# Disable Google Fonts download during build to prevent timeouts
ENV NEXT_FONT_GOOGLE_MOCKED=true

# Limit Node.js memory to prevent OOM on low-resource servers
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Build the application
RUN npm run build

# --- production stage ---
FROM node:20-alpine AS runner
WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set correct permissions
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set hostname
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# Health check using the /api/health endpoint (use 127.0.0.1 to avoid IPv6 issues)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/api/health || exit 1

# Start the application
CMD ["node", "server.js"]
