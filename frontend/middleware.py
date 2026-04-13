"""
JWT Auth Middleware for DHBW Gerätemanagement Frontend.
Reads JWT token and user info from session, injects into request.
"""


class JWTAuthMiddleware:
    """
    Middleware that reads the JWT token and current user from the session
    and injects them as request attributes.

    Sets:
        request.api_token: str | None  - JWT token for API calls
        request.current_user: dict | None - User info dict with keys:
            id, name, email, rolle, shibboleth_id
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Inject API token from session
        request.api_token = request.session.get('jwt_token', None)

        # Inject current user info from session
        request.current_user = request.session.get('user', None)

        response = self.get_response(request)
        return response
