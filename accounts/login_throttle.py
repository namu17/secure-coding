from django.conf import settings

from common.redis_client import get_redis_client


def _attempts_key(username):
    return f'login_attempts:{username}'


def _lockout_key(username):
    return f'login_lockout:{username}'


def is_login_locked(username):
    return get_redis_client().exists(_lockout_key(username)) == 1


def register_login_failure(username):
    redis_client = get_redis_client()
    key = _attempts_key(username)
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, settings.LOGIN_ATTEMPT_WINDOW_SECONDS)
    if count >= settings.LOGIN_MAX_ATTEMPTS:
        redis_client.setex(_lockout_key(username), settings.LOGIN_LOCKOUT_SECONDS, 1)
        redis_client.delete(key)


def clear_login_failures(username):
    redis_client = get_redis_client()
    redis_client.delete(_attempts_key(username))
    redis_client.delete(_lockout_key(username))
