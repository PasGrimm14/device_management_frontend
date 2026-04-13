"""
Authentication views for DHBW Gerätemanagement Frontend.
Handles login and logout.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from frontend.services.api_client import APIClient, APIError
from django.conf import settings


@require_http_methods(['GET', 'POST'])
def login_view(request):
    """
    Login page with shibboleth_id, name, email form (local test mode).
    On success: stores JWT token and user info in session, redirects to dashboard.
    """
    # Already logged in? Redirect to dashboard
    if request.api_token:
        return redirect('/')

    if request.method == 'POST':
        shibboleth_id = request.POST.get('shibboleth_id', '').strip()
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()

        # Basic validation
        if not shibboleth_id or not name or not email:
            messages.error(request, 'Bitte füllen Sie alle Felder aus.')
            return render(request, 'login.html', {
                'shibboleth_id': shibboleth_id,
                'name': name,
                'email': email,
            })

        try:
            client = APIClient(base_url=settings.API_BASE_URL)
            token_data = client.login(shibboleth_id=shibboleth_id, name=name, email=email)
            access_token = token_data.get('access_token')

            if not access_token:
                messages.error(request, 'Anmeldung fehlgeschlagen: Kein Token erhalten.')
                return render(request, 'login.html', {
                    'shibboleth_id': shibboleth_id,
                    'name': name,
                    'email': email,
                })

            # Fetch user profile with the new token
            authed_client = APIClient(base_url=settings.API_BASE_URL, token=access_token)
            user_data = authed_client.get_me()

            # Store in session
            request.session['jwt_token'] = access_token
            request.session['user'] = user_data
            request.session.modified = True

            messages.success(request, f'Willkommen, {user_data.get("name", name)}!')
            return redirect('/')

        except APIError as e:
            if e.status_code == 401:
                messages.error(request, 'Ungültige Anmeldedaten. Bitte überprüfen Sie Ihre Eingaben.')
            elif e.status_code == 422:
                messages.error(request, 'Ungültige Eingabe. Bitte überprüfen Sie Ihre Daten.')
            else:
                messages.error(request, f'Anmeldung fehlgeschlagen: {e.detail}')
            return render(request, 'login.html', {
                'shibboleth_id': shibboleth_id,
                'name': name,
                'email': email,
            })
        except Exception as e:
            messages.error(request, f'Verbindungsfehler: Der API-Server ist nicht erreichbar.')
            return render(request, 'login.html', {
                'shibboleth_id': shibboleth_id,
                'name': name,
                'email': email,
            })

    return render(request, 'login.html')


def logout_view(request):
    """Clears the session and redirects to login."""
    request.session.flush()
    messages.success(request, 'Sie wurden erfolgreich abgemeldet.')
    return redirect('/login/')
