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
            (rolle is overridden by active_role if set in session)
        request.real_role: str | None - The actual role from the DB (unchanged)
        request.active_role: str | None - The currently active role (may differ for admins)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Inject API token from session
        request.api_token = request.session.get('jwt_token', None)

        # Inject current user info from session
        user = request.session.get('user', None)
        request.real_role = user.get('rolle') if user else None

        # Determine active role: Admins can switch to user view
        if user and user.get('rolle') == 'Administrator':
            active_role = request.session.get('active_role', 'Administrator')
        else:
            # Non-admins always use their real role; clear any stale active_role
            active_role = user.get('rolle') if user else None
            if 'active_role' in request.session:
                del request.session['active_role']

        request.active_role = active_role

        # Expose a modified copy of the user dict so templates can use
        # request.current_user.rolle to get the *active* role naturally.
        # The real role is still accessible via request.real_role.
        if user:
            current_user = dict(user)
            current_user['rolle'] = active_role
            request.current_user = current_user
        else:
            request.current_user = None

        response = self.get_response(request)
        return response