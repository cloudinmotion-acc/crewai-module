FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    wget \
    iputils-ping \
    dnsutils \
    netcat-traditional \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home crew
WORKDIR /app
COPY requirements.txt .
COPY app/ ./app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
USER crew
EXPOSE 9100

HEALTHCHECK --interval=30s --timeout=5s \
    CMD curl -fsS http://127.0.0.1:9100/health || exit 1

CMD ["uvicorn", "app.crew.server:app", "--host", "0.0.0.0", "--port", "9100"]

