from functools import lru_cache

import redis
from django.conf import settings


@lru_cache
def get_redis_client():
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
