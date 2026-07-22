from django.conf import settings
from django.http import JsonResponse

from common.redis_client import get_redis_client

EXEMPT_PREFIXES = (settings.STATIC_URL, settings.MEDIA_URL)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(EXEMPT_PREFIXES):
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            key = f'ratelimit:{client_ip}'
            redis_client = get_redis_client()
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)
            if count > settings.RATE_LIMIT_MAX:
                return JsonResponse(
                    {'detail': 'Too many requests. Please try again later.'}, status=429
                )
        return self.get_response(request)
