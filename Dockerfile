# ---- Stage 1: Tailwind CSS build ----
FROM node:22-alpine AS assets
WORKDIR /build
COPY package.json package-lock.json* ./
RUN npm install
COPY tailwind.config.js postcss.config.js ./
COPY src ./src
COPY app/templates ./app/templates
COPY app/static/js ./app/static/js
RUN npm run build:css

# ---- Stage 2: Python runtime ----
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production \
    PATH="/home/allied/.local/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .
COPY --from=assets /build/app/static/css/main.css ./app/static/css/main.css

RUN mkdir -p /app/app/static/uploads /app/instance/invoices \
    && useradd --create-home --shell /bin/bash allied \
    && chown -R allied:allied /app

USER allied

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
