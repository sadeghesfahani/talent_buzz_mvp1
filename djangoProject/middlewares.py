from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthMiddleware(BaseMiddleware):
    """
    Token authentication middleware for Django Channels 2
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get('token', [None])[0]

        if token:
            # Authenticate the token and get the user
            jwt_auth = JWTAuthentication()
            try:
                validated_token = jwt_auth.get_validated_token(token)
                scope['user'] = await sync_to_async(jwt_auth.get_user, thread_sensitive=True)(validated_token)
            except Exception as e:
                scope['user'] = AnonymousUser()

        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)


# Convenience function to wrap the ASGI application with authentication middleware
def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
