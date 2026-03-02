# CrewAI Module

A lightweight FastAPI service that runs AI agents using the CrewAI framework. This module integrates with a **Model Router** (for inference) and **Redis** (for session state persistence) to provide a complete conversational AI system.

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites

- Python 3.9+
- Model Router running on `http://localhost:8000`
- Redis or AWS ElastiCache available
- curl or browser for testing

### 2. Install & Configure

```bash
# Clone and navigate to the project
cd /home/rhel/crewai-module

# Install dependencies
pip install -r requirements.txt

# Check that everything is properly configured
python verify_setup.py
```

You should see all tests marked as ✅ PASS.

### 3. Start the Server

```bash
# Run the FastAPI server
python -m uvicorn app.crew.server:app --reload --port 9100
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:9100
```

### 4. Test the Application

In a new terminal, send a test request:

```bash
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "input": "What is 2 + 2?",
    "model": "gpt-5-nano"
  }'
```

You should get back a JSON response with the AI's answer.

---

## 📋 What This Application Does

```
User Request
    ↓
CrewAI Agent receives your message
    ↓
Loads conversation history from Redis
    ↓
Calls Model Router for inference
    ↓
Saves updated conversation to Redis
    ↓
Returns the AI's response
```

**Key Features:**
- ✅ Maintains conversation history per session
- ✅ Multiple concurrent sessions
- ✅ Automatic Redis persistence
- ✅ Real-time inference via Model Router
- ✅ REST API + WebSocket support

---

## 🔧 Configuration

The application reads configuration from the `.env` file in the project root.

### Environment Variables

Create/edit `.env` file:

```dotenv
# Model Router (for AI inference)
MODEL_ROUTER_URL=http://localhost:8000

# Redis (for session state storage)
# Supports both standalone Redis and AWS ElastiCache Cluster
REDIS_HOST=clustercfg.test1h3march-redis-dev.gcvryk.use1.cache.amazonaws.com
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Optional: Session expiration (in seconds, default: 86400 = 24 hours)
SESSION_TTL=86400
```

**Note on Redis Cluster:** If using AWS ElastiCache Cluster, ensure `REDIS_HOST` is the **cluster configuration endpoint** (starts with `clustercfg.`), not individual node addresses. SSL/TLS is automatically enabled with certificate verification.

### Using Environment Variables Instead of .env

If you prefer to set variables directly (useful in Docker):

```bash
export MODEL_ROUTER_URL=http://localhost:8000
export REDIS_HOST=your-redis-host
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password

python -m uvicorn app.crew.server:app --port 9100
```

---

## 📖 API Endpoints

### POST /run
Send a message and get a response.

**Request:**
```bash
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user-123",
    "input": "Hello, how are you?",
    "model": "gpt-5-nano"
  }'
```

**Response:**
```json
{
  "response": "I'm doing well, thank you for asking!"
}
```

### GET /health
Check if the server is running.

```bash
curl http://localhost:9100/health
# Returns: {"status": "ok"}
```

### WebSocket /stream
Get streaming responses (advanced).

```bash
wscat -c ws://localhost:9100/stream
# Send: {"session_id": "s1", "input": "hello"}
```

---

## 🧪 Testing

### Verify Setup Works

Before running the server, verify all components are connected:

```bash
python verify_setup.py
```

This checks:
- ✅ Environment variables loaded
- ✅ Model Router accessible
- ✅ Redis connected
- ✅ Agent instantiated correctly

### Test Conversations

**Test 1: Single message**
```bash
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "input": "Hello", "model": "gpt-5-nano"}'
```

**Test 2: Multi-turn conversation (same session)**
```bash
# First message
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "chat1", "input": "My name is Alice"}'

# Second message (remembers context)
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "chat1", "input": "What is my name?"}'
```

**Test 3: Separate sessions**
```bash
# Session A
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "alice", "input": "I like cats"}'

# Session B (separate history)
curl -X POST http://localhost:9100/run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "bob", "input": "I like dogs"}'
```

---

## 🐳 Running with Docker

### Build the Docker Image

```bash
docker build -t crewai-module:v1 .
```

### Run the Container

```bash
docker run -d \
  -p 9100:9100 \
  -e MODEL_ROUTER_URL=http://host.docker.internal:8000 \
  -e REDIS_HOST=your-redis-host \
  -e REDIS_PORT=6379 \
  -e REDIS_PASSWORD=your_password \
  crewai-module:v1
```

Or use the `.env` file:

```bash
docker run -d -p 9100:9100 --env-file .env crewai-module:v1
```

---

## 🐛 Troubleshooting

### "Redis connection failed"
- Verify Redis is running and accessible
- Check `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD` in `.env`
- Test connection: `redis-cli -h <HOST> ping`

**Solution:**
```bash
# Check Redis is running
redis-cli -h your-redis-host ping

# Update .env with correct credentials
nano .env
```

### "Model Router unreachable"
- Verify Model Router is running on the configured port
- Check `MODEL_ROUTER_URL` in `.env`
- Test endpoint: `curl http://localhost:8000/health`

**Solution:**
```bash
# Start Model Router if not running
docker run -d -p 8000:8000 -e OPENAI_API_KEY=$KEY model-router:v1

# Or verify it's accessible
curl -X POST http://localhost:8000/generate \
  -d '{"prompt":"test", "model":"gpt-5-nano", "state":{}}'
```

### "Environment variables not loaded"
- Run `python verify_setup.py` to check what's loaded
- Make sure `.env` file is in the project root
- Use `export` if running shell commands directly

**Solution:**
```bash
# Check what's loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(f'HOST={os.getenv(\"REDIS_HOST\")}')"
```

### See More Help
Detailed troubleshooting guide: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## 📚 Advanced Usage

### Project Structure

```
crewai-module/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container definition
├── .env                          # Configuration (create this)
├── verify_setup.py               # Verification script
└── app/
    ├── __init__.py
    ├── agents/
    │   └── crewai_agent.py       # Main agent logic
    ├── crew/
    │   ├── server.py             # FastAPI HTTP server
    │   ├── agent.py              # Agent factory
    │   ├── config.py             # Configuration loading
    │   ├── memory.py             # Session storage (Redis)
    │   ├── router.py             # Model Router client
    │   └── tests/                # Unit tests
    ├── memory/
    │   └── redis.py              # Redis implementation
    └── router/
        └── client.py             # Model Router HTTP client
```

### Using the CLI

The application includes a command-line interface for development:

```bash
# Interactive mode
python -m app.crew.runner run

# Session replay
python -m app.crew.runner replay session-123

# Load persona
python -m app.crew.runner load_persona /path/to/persona.yaml
```

### Custom Memory Backend

Store session state somewhere other than Redis:

```python
from app.crew.memory import InMemoryMemory
from app.crew.agent import create_agent

# Use in-memory storage instead of Redis
agent = create_agent(
    model_router_url="http://localhost:8000",
    memory=InMemoryMemory()  # Great for testing
)
```

### Adding Plugins

Extend functionality with plugins that run before/after each request:

```python
from app.crew.plugins import Plugin

class CustomPlugin(Plugin):
    async def run(self, context):
        # Modify context or call external services
        context["custom_field"] = "custom_value"
```

---

## 💡 Quick Reference

| Task | Command |
|------|---------|
| Check setup | `python verify_setup.py` |
| Start server | `python -m uvicorn app.crew.server:app --reload --port 9100` |
| Test endpoint | `curl -X POST http://localhost:9100/run -H "Content-Type: application/json" -d '{"session_id":"test","input":"hello"}'` |
| Check health | `curl http://localhost:9100/health` |
| Inspect logs | `docker logs -f <container_id>` |
| Build Docker | `docker build -t crewai-module:v1 .` |
| Run Docker | `docker run -d -p 9100:910000 --env-file .env crewai-module:v1` |
| Interactive CLI | `python -m app.crew.runner run` |

---

