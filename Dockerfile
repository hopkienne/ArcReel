# ============================================================
# Stage 1: Build frontend
# ============================================================
FROM node:22-slim AS frontend-builder

WORKDIR /build/frontend

# Cài đặt pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Sao chép tệp phụ thuộc trước để tận dụng cache
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Sao chép mã nguồn frontend và build
COPY frontend/ ./
RUN pnpm build

# ============================================================
# Stage 2: Production image
# ============================================================
FROM python:3.12-slim AS production

# Cài đặt phụ thuộc hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Tắt bộ đệm stdout của Python để log được ghi realtime vào Docker logs
ENV PYTHONUNBUFFERED=1

# Sao chép trước phụ thuộc và metadata gói để tận dụng cache
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev --no-install-project

# Sao chép mã ứng dụng
COPY lib/ lib/
COPY server/ server/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY scripts/ scripts/
COPY agent_runtime_profile/ agent_runtime_profile/
COPY public/ public/

# Sao chép artifact build frontend
COPY --from=frontend-builder /build/frontend/dist/ frontend/dist/

# Tạo thư mục runtime
RUN mkdir -p projects vertex_keys

# Mở cổng
EXPOSE 1241

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:1241/health || exit 1

# Lệnh khởi động
CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "1241"]
