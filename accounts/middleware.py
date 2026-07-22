import jwt
from django.contrib.auth.models import AnonymousUser

from accounts.jwt_utils import ACCESS_COOKIE, decode_token
from accounts.models import User


class JWTAuthenticationMiddleware:
    """Populates request.user from the access-token cookie for the public
    site. Leaves request.user untouched if a session already authenticated
    it (i.e. /admin/ logins), so admin auth keeps working unmodified.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(request.user, 'is_authenticated', False):
            token = request.COOKIES.get(ACCESS_COOKIE)
            if token:
                try:
                    payload = decode_token(token)
                    if payload.get('type') == 'access':
                        request.user = User.objects.get(pk=payload['user_id'])
                except (jwt.InvalidTokenError, User.DoesNotExist):
                    request.user = AnonymousUser()
        return self.get_response(request)
