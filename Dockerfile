# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy source code
COPY . /app/

# IMPORTANT: Build Tailwind
# This generates the file that was "Not Found"
RUN python manage.py tailwind install --no-input
RUN python manage.py tailwind build --no-input

# Collect Static (Organizes files for WhiteNoise)
RUN python manage.py collectstatic --noinput

# --- Stage 2: Runtime ---
FROM python:3.12-slim

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y libmariadb3 && rm -rf /var/lib/apt/lists/*

# Copy python packages and the ENTIRE app (including built CSS) from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]