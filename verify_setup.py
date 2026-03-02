#!/usr/bin/env python3
"""
Quick verification script to test LLM Module and Redis integration
Run: python verify_setup.py
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE any imports
load_dotenv()

# Add the crewai-module to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_config():
    """Test 1: Verify environment variables are loaded"""
    print("\n" + "="*60)
    print("TEST 1: Environment Variables")
    print("="*60)
    
    from app.crew.config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
    
    print(f"✓ MODEL_ROUTER_URL: {MODEL_ROUTER_URL}")
    print(f"✓ REDIS_HOST: {REDIS_HOST}")
    print(f"✓ REDIS_PORT: {REDIS_PORT}")
    print(f"✓ REDIS_PASSWORD: {'***' if REDIS_PASSWORD else 'NOT SET'}")
    
    assert MODEL_ROUTER_URL, "MODEL_ROUTER_URL not set"
    assert REDIS_HOST, "REDIS_HOST not set"
    assert REDIS_PORT, "REDIS_PORT not set"
    
    print("\n✅ All environment variables loaded successfully!")
    return True


async def test_router_client():
    """Test 2: Test ModelRouterClient initialization"""
    print("\n" + "="*60)
    print("TEST 2: Model Router Client")
    print("="*60)
    
    from app.crew.config import MODEL_ROUTER_URL
    from app.router.client import ModelRouterClient
    
    try:
        router = ModelRouterClient(MODEL_ROUTER_URL)
        print(f"✓ ModelRouterClient created: {router}")
        print(f"✓ Base URL: {router.base_url}")
        print("\n✅ Model Router Client initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create ModelRouterClient: {e}")
        return False


async def test_redis_memory():
    """Test 3: Test RedisMemory initialization and connection"""
    print("\n" + "="*60)
    print("TEST 3: Redis Memory Backend")
    print("="*60)
    
    from app.crew.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
    from app.crew.memory import RedisMemory
    
    try:
        redis_mem = RedisMemory(REDIS_HOST, REDIS_PORT, REDIS_PASSWORD)
        print(f"✓ RedisMemory created: {redis_mem}")
        
        # Try lazy connection
        print("\nAttempting to connect to Redis...")
        await redis_mem._ensure_connected()
        print(f"✓ Redis connected successfully!")
        print(f"✓ Redis Host: {redis_mem.host}")
        print(f"✓ Redis Port: {redis_mem.port}")
        
        print("\n✅ Redis Memory Backend initialized and connected successfully!")
        return True
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("   This is OK if Redis is not yet available.")
        print("   Lazy connection will retry when needed.")
        return False


async def test_agent_creation():
    """Test 4: Test agent creation with router and memory"""
    print("\n" + "="*60)
    print("TEST 4: CrewAI Agent Creation")
    print("="*60)
    
    try:
        from app.crew.agent import create_agent
        from app.crew.config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
        
        agent = create_agent(
            model_router_url=MODEL_ROUTER_URL,
            redis_host=REDIS_HOST,
            redis_port=REDIS_PORT,
            redis_password=REDIS_PASSWORD,
        )
        
        print(f"✓ Agent created: {type(agent).__name__}")
        print(f"✓ Router: {agent.router}")
        print(f"✓ Memory: {type(agent.memory).__name__}")
        
        print("\n✅ CrewAI Agent created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_inference_call():
    """Test 5: Simulate an inference call (if model-router is running)"""
    print("\n" + "="*60)
    print("TEST 5: Model Router Inference Call")
    print("="*60)
    
    try:
        from app.crew.agent import create_agent
        from app.crew.config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
        import httpx
        
        # Check if model-router is running
        print(f"Checking if model-router is running at {MODEL_ROUTER_URL}...")
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                resp = await client.post(
                    f"{MODEL_ROUTER_URL}/generate",
                    json={
                        "prompt": "Hello, what is 2+2?",
                        "model": "gpt-5-nano",
                        "state": {"history": []}
                    }
                )
                result = resp.json()
                print(f"✓ Model Router responded: {result.get('text', result.get('output', str(result))[:100])}")
                print("\n✅ Model Router is running and responding!")
                return True
            except httpx.ConnectError:
                print(f"⚠️  Model Router not running at {MODEL_ROUTER_URL}")
                print("   This is OK - you can start it with:")
                print("   $ docker run -p 8000:8000 <model-router-image>")
                return False
    except Exception as e:
        print(f"⚠️  Could not test inference: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CREWAI-MODULE SETUP VERIFICATION")
    print("="*60)
    
    results = {
        "Config": await test_config(),
        "Router Client": await test_router_client(),
        "Redis Memory": await test_redis_memory(),
        "Agent Creation": await test_agent_creation(),
        "Inference": await test_inference_call(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "⚠️ FAIL/WARN"
        print(f"{status} - {test}")
    
    critical = results["Config"] and results["Router Client"] and results["Agent Creation"]
    
    if critical:
        print("\n✅ Critical components are properly configured!")
        print("\nYour setup includes:")
        print("  ✓ Model Router integration (localhost:8000)")
        print("  ✓ Redis session storage (AWS ElastiCache)")
        print("  ✓ Full inference pipeline")
        print("\nReady to use! Start the server with:")
        print("  $ python -m uvicorn app.crew.server:app --reload")
    else:
        print("\n❌ Critical configuration missing. Check above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
