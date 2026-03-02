# Troubleshooting Guide - CrewAI Module Integration

## Quick Diagnostics

Run the verification script to diagnose all issues:
```bash
cd /home/rhel/crewai-module
python verify_setup.py
```

This will check:
- ✓ Environment variables loading
- ✓ Model Router connectivity
- ✓ Redis connection
- ✓ Agent creation
- ✓ Inference capability

---

## Common Issues & Solutions

### 1. Redis Connection Failed

**Symptom:**
```
Redis connection attempt 1/5 failed: Error [Errno 111] Connection refused
Failed to connect to Redis after 5 attempts
```

**Note:** RedisMemory automatically retries 5 times with 10-second delays before failing.

**Root Causes & Solutions:**

#### A. Redis Not Running
```bash
# Check if Redis is running
redis-cli -h clustercfg.test1h3march-redis-dev.gcvryk.use1.cache.amazonaws.com ping

# If using AWS ElastiCache, verify cluster is running:
aws elasticache describe-cache-clusters --query 'CacheClusters[*].[CacheClusterIdentifier,CacheClusterStatus]'
```

#### B. Wrong Credentials
```bash
# Verify REDIS_HOST in .env is complete URL, not just hostname
# Should be: clustercfg.test1h3march-redis-dev.gcvryk.use1.cache.amazonaws.com
# NOT: redis-dev.gcvryk.use1.cache.amazonaws.com

# Check password is correct
cat /home/rhel/crewai-module/.env | grep REDIS_
```

#### C. Security Group Issue (AWS)
```bash
# Verify ElastiCache security group allows your IP on port 6379
# In AWS Console:
# 1. Go to ElastiCache → Clusters
# 2. Click your cluster
# 3. Check Security Group → Inbound Rules
# 4. Port 6379 should be open to your security group

# Quick check: Try connecting via redis-cli
redis-cli -h <redis-host> -p 6379 -a <password> ping
```

#### D. Network Connectivity
```bash
# Is the endpoint reachable?
nc -zv clustercfg.test1h3march-redis-dev.gcvryk.use1.cache.amazonaws.com 6379

# Check from container if running Docker
docker exec <container_id> nc -zv <redis-host> 6379
```

#### E. Redis Cluster Mode Issues (AWS ElastiCache)

**Symptom:**
```
MovedError: 13355 <other-node>
ASK error
Cluster topology changed
```

**Solution:**
For AWS ElastiCache Cluster, RedisMemory uses `skip_full_coverage_check=True` and handles topology changes automatically. Ensure:

```bash
# 1. REDIS_HOST is the cluster CONFIGURATION endpoint
# Correct: clustercfg.test1h3march-redis-dev.gcvryk.use1.cache.amazonaws.com
# Wrong: test1h3march-redis-dev.gcvryk.use1.cache.amazonaws.com

cat /home/rhel/crewai-module/.env | grep REDIS_HOST

# 2. SSL/TLS is automatically enabled - ensure port 6379 is accessible
unix_timestamp=$(date +%s)
echo "Timestamp: $unix_timestamp"
```

**Fix:**
```bash
# Update .env with correct credentials
export REDIS_HOST=clustercfg.test1h3march-redis-dev.gcvryk.use1.cache.amazonaws.com
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password_here

# Or update .env file directly
nano /home/rhel/crewai-module/.env

# Then restart your service
```

#### F. Redis SSL/TLS Certificate Issues

**Symptom:**
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
Connection closed by remote host
```

**Solution:**
RedisMemory automatically handles SSL/TLS with certifi CA bundle. If you see certificate errors:

```bash
# 1. Verify certifi is installed
pip list | grep certifi

# 2. Explicitly test SSL connection
python -c "
import ssl
from certifi import where
ssl_context = ssl.create_default_context(cafile=where())
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED
print('✓ SSL context created successfully')
"

# 3. For AWS ElastiCache, SSL/TLS is required (always enabled)
```

---

### 2. Model Router Not Responding

**Symptom:**
```
Failed to connect to ModelRouter at http://localhost:8000
ModelRouter service unavailable
```

**Root Causes & Solutions:**

#### A. Model Router Not Running
```bash
# Check if model-router is running on port 8000
curl -s http://localhost:8000/health | python -m json.tool

# If not running, start it
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  <model-router-image>

# Or if running locally:
python -m model_router.server --port 8000
```

#### B. Wrong Port/Host
```bash
# Check MODEL_ROUTER_URL in .env
cat /home/rhel/crewai-module/.env | grep MODEL_ROUTER

# Should be: http://localhost:8000
# Or: http://<hostname>:8000
```

#### C. Model Router Behind Firewall
```bash
# Test connectivity
curl -v http://localhost:8000/health

# If in Docker, check if container ports are published
docker ps | grep model-router

# Should show: 8000->8000
```

#### D. API Key Issues
```bash
# Model Router might need API key
# Check if inference is failing due to missing OPENAI_API_KEY

docker logs <model-router-container-id> | grep -i "key\|auth\|api"

# Set API key in model-router container
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  <model-router-image>
```

**Fix:**
```bash
# Verify model-router is accessible
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "test",
    "model": "gpt-5-nano",
    "state": {}
  }'

# Should return JSON with response/text field
```

---

### 3. Environment Variables Not Loaded

**Symptom:**
```
REDIS_HOST: localhost  # Should be AWS endpoint
MODEL_ROUTER_URL: None
```

**Root Causes:**

The .env file is not being loaded before imports.

**Solution:**

Ensure `load_dotenv()` is called BEFORE any config imports:

```python
# WRONG - config imported first
from app.crew.config import MODEL_ROUTER_URL
load_dotenv()

# RIGHT - load_dotenv called first
load_dotenv()
from app.crew.config import MODEL_ROUTER_URL
```

**Check your imports:**
```bash
# In server.py (should be fine now)
grep -n "load_dotenv\|from.*config" /home/rhel/crewai-module/app/crew/server.py | head -5

# Should show load_dotenv() before config import
```

**Fix:**
```bash
# If running custom scripts, always call load_dotenv() first
python -c "from dotenv import load_dotenv; load_dotenv(); from app.crew.config import *; print('OK')"

# Verify it loads correctly
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(f'REDIS_HOST={os.getenv(\"REDIS_HOST\")}')"
```

---

### 4. State Not Persisting in Redis

**Symptom:**
```
❌ No data in Redis
Session doesn't persist between requests
```

**Debug Steps:**

```bash
# 1. Check if Redis is storing data
redis-cli -h <redis-host> -a <password> keys "state:*"

# 2. Should return keys like: state:session-123

# 3. Get the actual state
redis-cli -h <redis-host> -a <password> GET "state:test-session"

# 4. Check TTL (should be 86400 seconds = 24 hours)
redis-cli -h <redis-host> -a <password> TTL "state:test-session"
```

**Common Issues:**

#### A. Inference Failed, State Not Saved
```bash
# Check logs for errors during inference
python -m uvicorn app.crew.server:app --reload --log-level=debug 2>&1 | grep -i "error\|exception"

# Look for:
# "Error in CrewAIAgent.run: ..."
# "Failed to set key ... in Redis"
```

#### B. JSON Encoding Issue
```bash
# State should be valid JSON
redis-cli -h <redis-host> -a <password> GET "state:session-id" | python -m json.tool

# If invalid JSON, check what's being saved in crewai_agent.py
```

#### C. Redis Memory Full
```bash
# Check Redis memory usage
redis-cli -h <redis-host> -a <password> info memory

# Check max memory policy
redis-cli -h <redis-host> -a <password> CONFIG GET maxmemory-policy

# If needed, increase memory or set cleanup policy:
redis-cli -h <redis-host> -a <password> CONFIG SET maxmemory-policy "allkeys-lru"
```

**Fix:**

```bash
# 1. Verify inference is succeeding (check logs)
# 2. Verify Redis is accepting writes:
redis-cli -h <redis-host> -a <password> SET test "value" && echo "✓ Redis is writable"

# 3. Verify session key format is "state:{session_id}"
# 4. Test end-to-end:
python verify_setup.py
```

---

### 5. Slow Inference Response

**Symptom:**
```
Request takes 30+ seconds to complete
HTTP timeout errors
```

**Potential Issues:**

```bash
# 1. Check Model Router performance
time curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "model": "gpt-5-nano", "state": {}}'

# Should complete in < 5 seconds

# 2. Check Redis latency
redis-cli -h <redis-host> -a <password> --latency

# Should be < 10ms for local, < 50ms for AWS regions

# 3. Check network connectivity
ping <redis-host>
ping <model-router-host>

# 4. Monitor full request flow:
python -m uvicorn app.crew.server:app --reload --log-level=debug

# Look for timing between:
# - "Calling model-router..."
# - "Received response from model-router"
# - "State saved to Redis"
```

**Potential Solutions:**

```bash
# 1. Increase timeout in router client (in app/router/client.py)
# Change: timeout=30.0 to timeout=60.0

# 2. Use connection pooling (already using httpx.AsyncClient)

# 3. Increase Redis socket timeout in config:
# REDIS_SOCKET_TIMEOUT=30 in .env
```

---

### 6. Docker Container Issues

**Symptom:**
```
Container exits immediately
No logs
```

**Debug:**

```bash
# Check logs
docker logs <container_id>

# View recent logs
docker logs --tail 50 <container_id>

# Real-time logs
docker logs -f <container_id>

# If container keeps crashing, start it with shell
docker run -it <image> /bin/bash

# Then manually test
cd /app
python verify_setup.py
python -m uvicorn app.crew.server:app --host 0.0.0.0 --port 8000
```

**Common Docker Issues:**

#### A. Environment Variables Not Passed
```bash
# Wrong - env vars not available in container
docker run -p 8000:8000 crewai-module:latest

# Right - pass env vars explicitly
docker run -p 8000:8000 \
  -e REDIS_HOST=$REDIS_HOST \
  -e REDIS_PORT=$REDIS_PORT \
  -e REDIS_PASSWORD=$REDIS_PASSWORD \
  -e MODEL_ROUTER_URL=http://host.docker.internal:8000 \
  crewai-module:latest

# Or use --env-file
docker run -p 8000:8000 --env-file .env crewai-module:latest
```

#### B. Network Connectivity in Docker
```bash
# From inside container, model-router might not be on localhost:8000
# Instead use host.docker.internal (Mac/Windows) or host IP (Linux)

docker run -p 8000:8000 \
  -e MODEL_ROUTER_URL=http://host.docker.internal:8000 \
  crewai-module:latest

# On Linux, use the host IP instead
docker run -p 8000:8000 \
  -e MODEL_ROUTER_URL=http://172.17.0.1:8000 \
  crewai-module:latest
```

---

### 7. Memory Leaks

**Symptom:**
```
Memory usage grows over time
Eventually crashes with OOMKilled
```

**Monitor:**

```bash
# Check current memory usage
ps aux | grep python | grep uvicorn

# Monitor over time
watch -n 1 'ps aux | grep uvicorn | grep -v grep'

# Or use container stats
docker stats <container_id>
```

**Common Causes:**

```python
# 1. Unclosed HTTP connections in router client
# (Should be fixed by using async context manager)

# 2. Large conversation histories in Redis
# Monitor with:
redis-cli -h <host> -a <password> --scan | wc -l

# 3. Python memory not released
# Can add garbage collection hints:
import gc
gc.collect()  # After processing request
```

---

## Health Checks

### Manual Health Check
```bash
curl http://localhost:8000/health
# Returns: {"status": "ok"}
```

### Docker Health Check
Add to Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1
```

### Kubernetes Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
```

---

## Metrics & Monitoring

### Key Metrics to Monitor

1. **Model Router Latency** (time to inference)
```bash
# In logs, look for:
# "Calling model-router... / Received response from model-router"
```

2. **Redis Connection Health**
```bash
redis-cli -h <host> -a <password> ping
# Should return: PONG
```

3. **Session Count**
```bash
redis-cli -h <host> -a <password> keys "state:*" | wc -l
```

4. **Error Rate**
```bash
# Check logs for exceptions
docker logs <container> 2>&1 | grep -i "error" | wc -l
```

### Prometheus Metrics (Optional)

Add to requirements.txt:
```
prometheus-client
```

Then in server.py:
```python
from prometheus_client import Counter, Histogram
import time

request_count = Counter('requests_total', 'Total requests')
inference_time = Histogram('inference_seconds', 'Inference latency')

@app.post("/run")
async def run_crewai(request: CrewRequest):
    request_count.inc()
    start = time.time()
    # ... your code ...
    inference_time.observe(time.time() - start)
```

---

## Getting Help

If you're still stuck:

1. **Run verification script** to get a full diagnostic:
   ```bash
   python verify_setup.py
   ```

2. **Check logs** with full debug output:
   ```bash
   python -m uvicorn app.crew.server:app --log-level=debug
   ```

3. **Test each component** separately:
   ```bash
   # Redis
   redis-cli -h <host> -a <pass> ping
   
   # Model Router  
   curl -X POST http://localhost:8000/generate \
     -d '{"prompt":"test", "model":"gpt-5-nano", "state":{}}'
   
   # Agent
   python verify_setup.py
   ```

4. **Check configuration**:
   ```bash
   cat /home/rhel/crewai-module/.env
   ```

---

## Technologies Used

### Redis Cluster Configuration

RedisMemory uses **synchronous `RedisCluster`** from the `redis` library with async-safe wrapping:

```python
# In app/crew/memory.py
from redis.cluster import RedisCluster
import asyncio

class RedisMemory(MemoryBackend):
    def __init__(self, host, port, password, max_retries=5, retry_delay=10):
        self._client = None  # Created on first use
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def _ensure_connected(self):
        # Runs synchronously with SSL/TLS
        ssl_context = create_default_context(cafile=certifi.where())
        self._client = RedisCluster(
            host, port, password,
            ssl=True,
            ssl_context=ssl_context,
            skip_full_coverage_check=True  # For AWS ElastiCache Cluster
        )
    
    async def get(self, key):
        # Wrapped in executor for non-blocking async operation
        await asyncio.get_event_loop().run_in_executor(
            None, self._client.get, key
        )
```

**Why synchronous client?** AWS ElastiCache Cluster properly supports the synchronous RedisCluster client, while async variants have limitations with cluster topology changes.

## Summary Checklist

- [ ] `.env` file exists with correct format
- [ ] Model Router is running on configured port
- [ ] Redis credentials are accessible
- [ ] `REDIS_HOST` is the **cluster configuration endpoint** (if using AWS ElastiCache)
- [ ] `load_dotenv()` is called before config imports
- [ ] `verify_setup.py` shows all ✅ PASS
- [ ] Server starts without errors
- [ ] State persists in Redis
- [ ] Inference calls complete successfully
- [ ] SSL/TLS connection established (auto-verified)
- [ ] Multi-turn conversations preserve context
- [ ] Logs show "✅ Received response from model-router"

All checks passing? You're ready to go! 🎉
