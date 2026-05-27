
import json
import  redis.asyncio as aioredis
from config import Config
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request,Response
redis=aioredis.from_url(Config.REDIS_URL)

class CustomMiddleWare(BaseHTTPMiddleware):
    async def dispatch(self,request:Request,call_next):
        if request.method in ["POST","PATCH"] and "/transaction" in request.url.path:
            idempotency_key=request.headers.get("X-Idempotency-Key")
            if not idempotency_key:
                return  await call_next(request)
            cache_key=f"idempotency:{idempotency_key}"
            lock_key=f"lock:{idempotency_key}"
            cached_response=await redis.get(cache_key)
            
            if cached_response:
                
                data=json.loads(cached_response)
                return Response(content=data["body"],status_code=data["status_code"],headers={"X-Cache-Lookup": "HIT", "Content-Type": "application/json"})
            acquired_lock=await redis.set(lock_key,"locked",nx=True,ex=10)
            if not acquired_lock:
                return Response(content=json.dumps({"detail":"an identical request is already being processed . please wait"}),status_code=409,headers={"Content-Type": "application/json"})
            try:
                response=await call_next(request)

                if response.status_code<500:
                    response__body=b""
                    async for chunk in response.body_iterator:
                        response__body+=chunk
                    payload_to_cache={
                        "status_code":response.status_code,"body":response__body.decode("utf-8")
                    }
                    await redis.set(cache_key,json.dumps(payload_to_cache),ex=86400)
                    return Response(content=response__body,status_code=response.status_code,headers=dict(response.headers))
                return response
            finally:
                await redis.delete(lock_key)

        return await call_next(request)
             

            


