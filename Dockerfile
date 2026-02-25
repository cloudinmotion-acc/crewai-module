# This Dockerfile builds a lightweight image containing only the
# CrewAI module and its minimal dependencies.  It assumes the
# `agent-runtime` package is accessible via a local path or installed
# from PyPI (if you choose to publish it).
#
# Usage (from repo root):
#   docker build -f crew/Dockerfile -t crewai-server:latest .
#
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install any OS packages needed by Redis client / httpx etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /crew

# copy only the parts required for crew; keep the build context small
COPY crew/requirements.txt ./requirements.txt
COPY crew/crew ./crew

# if the agent-runtime is required as a package, copy it too; otherwise
# your build process should `pip install` it separately (e.g. from PyPI)
COPY app ./app

RUN pip install --no-cache-dir -r requirements.txt

# expose port used by the standalone CrewAI server
EXPOSE 9100

# default to running the crew/server module; override CMD if needed
CMD ["uvicorn", "crew.server:app", "--host", "0.0.0.0", "--port", "9100"]
