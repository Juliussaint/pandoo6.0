# --- Stage 1: Builder (Python + Node for Tailwind) ---
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build tools + Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy everything to build Tailwind
COPY . /app/

# 1. Install Tailwind (NPM) dependencies
# Assuming your tailwind app is named 'theme' (default for django-tailwind)
# If your theme folder is different, adjust the path below
RUN python manage.py tailwind install

# 2. Build the production CSS
RUN python manage.py tailwind build

# 3. Collect all static files
# Make sure STATIC_ROOT is defined in your settings.py
RUN python manage.py collectstatic --noinput


# --- Stage 2: Runtime (Clean & Small) ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Only install runtime libraries (No build tools, no Node.js needed here)
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy the entire project (including the compiled static files from builder)
COPY --from=builder /app /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]