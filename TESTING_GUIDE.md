# Local Testing Guide for CrewAI Module

## Prerequisites
- Python 3.11+ installed
- Access to model-router service (URL needed)
- Access to Redis instance (host, port, password needed)

## Step 1: Install Dependencies

```bash
# From the repository root
pip install -r requirements.txt
```

This installs all required packages including FastAPI, uvicorn, redis, typer, etc.

## Step 2: Set Environment Variables

```bash
# Set these based on your actual services
export MODEL_ROUTER_URL="http://localhost:8000"  # or your actual model-router URL
export REDIS_HOST="localhost"                     # or your Redis host
export REDIS_PORT="6379"                          # or your Redis port
export REDIS_PASSWORD=""                          # or your Redis password if needed
```

On Windows PowerShell:
```powershell
$env:MODEL_ROUTER_URL = "http://localhost:8000"
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:REDIS_PASSWORD = ""
```

## Step 3: Verify Configuration

```bash
python -c "
import sys
sys.path.append('app')
from crew.config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
print('MODEL_ROUTER_URL:', MODEL_ROUTER_URL)
print('REDIS_HOST:', REDIS_HOST)
print('REDIS_PORT:', REDIS_PORT)
print('REDIS_PASSWORD:', REDIS_PASSWORD if REDIS_PASSWORD else '(not set)')
"
```

This confirms configuration is loaded correctly.

## Step 4: Start the Server

```bash
# Option A: Using the CLI helper (recommended)
python -m crew.runner serve --host 127.0.0.1 --port 9100

# Option B: Direct uvicorn
cd app/crew && uvicorn server:app --host 127.0.0.1 --port 9100
```

You should see output like:
```
starting server on 127.0.0.1:9100, reload=False
INFO:     Uvicorn running on http://127.0.0.1:9100
```

## Step 5: Test the Health Endpoint

In a new terminal:

```bash
curl -X GET http://localhost:9100/health
```

Expected response:
```json
{"status":"ok"}
```

## Step 6: Test the Run Endpoint

```bash
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-1","input":"Hello, what is your name?"}'
```

This should return a JSON response with the agent's output.

## Step 7: Test Session Persistence

Make another request with the same session_id:

```bash
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-1","input":"What did I just ask you?"}'
```

The agent should have context from the previous turn.

## Step 8: Test WebSocket Streaming (Optional)

Using `websocat` or another WebSocket client:

```bash
# Install websocat if you don't have it
# macOS: brew install websocat
# Other: https://github.com/vi/websocat

websocat ws://localhost:9100/stream
# Then send: {"session_id":"test-2","input":"Hello"}
```

You should see chunks streaming back.

## Troubleshooting

- **"Connection refused"**: Ensure the server is running and listening on the correct port
- **"Redis connection error"**: Check that Redis is running and credentials are correct
- **"Model router error"**: Ensure MODEL_ROUTER_URL is reachable and the service is running
- **"Module import error"**: Ensure `app` directory is on PYTHONPATH (conftest.py handles this if running from repo root)

## Next: Once Testing Succeeds
Once all endpoints work:
1. Stop the server (Ctrl+C in terminal)
2. Proceed to Docker image build
3. Test the container locally
4. Finally, deploy to Kubernetes
