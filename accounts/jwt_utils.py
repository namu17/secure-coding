import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings

from common.redis_client import get_redis_client

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'


def _encode(user, ttl, token_type):
    now = datetime.now(timezone.utc)
    payload = {
        'user_id': user.id,
        'role': user.role,
        'type': token_type,
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + ttl,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, payload


def issue_tokens(user):
    access_token, access_payload = _encode(
        user, timedelta(minutes=settings.JWT_ACCESS_TTL_MIN), 'access'
    )
    refresh_token, refresh_payload = _encode(
        user, timedelta(days=settings.JWT_REFRESH_TTL_DAYS), 'refresh'
    )

    redis_client = get_redis_client()
    refresh_ttl_seconds = settings.JWT_REFRESH_TTL_DAYS * 24 * 60 * 60
    redis_client.setex(f'refresh:{refresh_payload["jti"]}', refresh_ttl_seconds, user.id)

    return access_token, refresh_token


def decode_token(token):
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    redis_client = get_redis_client()
    if redis_client.exists(f'blacklist:{payload["jti"]}'):
        raise jwt.InvalidTokenError('Token has been revoked')
    return payload


def blacklist_token(payload):
    redis_client = get_redis_client()
    now = datetime.now(timezone.utc)
    exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    remaining = max(int((exp - now).total_seconds()), 1)
    redis_client.setex(f'blacklist:{payload["jti"]}', remaining, 1)


def revoke_refresh_token(jti):
    redis_client = get_redis_client()
    redis_client.delete(f'refresh:{jti}')


def is_refresh_token_valid(jti):
    redis_client = get_redis_client()
    return redis_client.exists(f'refresh:{jti}') == 1


def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.JWT_ACCESS_TTL_MIN * 60,
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.JWT_REFRESH_TTL_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )


def clear_auth_cookies(response):
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE)
