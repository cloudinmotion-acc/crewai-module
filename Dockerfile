# This Dockerfile builds a lightweight image containing only the
# CrewAI module and its minimal dependencies.  The application code is
# stored under `app/crew` in the repository; the container sets `/app`
# as its working directory so `import crew` works automatically.  The
# `crewai` runtime package is installed via pip from requirements.
#
# Usage (from repo root):
#   docker build -f Dockerfile -t crewai-server:latest .
#
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
WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY app/crew ./crew
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 9100
CMD ["uvicorn", "crew.server:app", "--host", "0.0.0.0", "--port", "9100"]