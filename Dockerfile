# ================================
# Stage 1 — Builder (Python + Node)
# ================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy project
COPY . /app/

# ------------------------
# Build Tailwind CSS
# ------------------------
WORKDIR /app/theme/static_src
RUN npm install --no-audit --no-fund
RUN npm run build

# Back to root
WORKDIR /app


# ================================
# Stage 2 — Runtime (lean image)
# ================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy app with built CSS
COPY --from=builder /app /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
