from http.cookies import SimpleCookie

import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from accounts.jwt_utils import ACCESS_COOKIE, decode_token


@database_sync_to_async
def _get_user(user_id):
    from accounts.models import User

    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Authenticates WebSocket connections using the same access_token
    cookie the rest of the site uses (see accounts/middleware.py).
    """

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get('headers', []))
        raw_cookie = headers.get(b'cookie', b'').decode()
        cookies = SimpleCookie()
        cookies.load(raw_cookie)

        scope['user'] = AnonymousUser()
        token_morsel = cookies.get(ACCESS_COOKIE)
        if token_morsel:
            try:
                payload = decode_token(token_morsel.value)
                if payload.get('type') == 'access':
                    scope['user'] = await _get_user(payload['user_id'])
            except jwt.InvalidTokenError:
                pass

        return await super().__call__(scope, receive, send)
