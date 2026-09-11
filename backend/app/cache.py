"""Redis Caching Layer for SafeHabitat AI.

Caches frequent API responses to reduce latency.
"""

import hashlib
import json
import os
from functools import wraps

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = 300  # 5 minutes

_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global _client
    if _client is None:
        try:
            _client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
            _client.ping()
        except Exception:
            _client = None
    return _client


def cache_response(ttl: int = CACHE_TTL, prefix: str = "api"):
    """Decorator to cache API responses in Redis."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            r = get_redis()
            if r is None:
                return func(*args, **kwargs)

            # Build cache key from function name + args + kwargs
            key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

            # Try cache hit
            try:
                cached = r.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

            # Cache miss - compute and store
            result = func(*args, **kwargs)
            try:
                r.setex(cache_key, ttl, json.dumps(result, default=str))
            except Exception:
                pass

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str = "api:*"):
    """Clear cache entries matching pattern."""
    r = get_redis()
    if r:
        try:
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
        except Exception:
            pass


def cache_stats() -> dict:
    """Get cache hit/miss statistics."""
    r = get_redis()
    if not r:
        return {"status": "disconnected"}
    try:
        info = r.info("stats")
        return {
            "status": "connected",
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": round(
                info.get("keyspace_hits", 0)
                / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
                * 100,
                2,
            ),
        }
    except Exception:
        return {"status": "error"}
