"""
SSO Callback View für DHBW Geräteverwaltung.
Wird aufgerufen wenn ein User von sg-gerätemanagement weitergeleitet wird.
"""

from django.shortcuts import redirect
from django.conf import settings
from frontend.services.api_client import APIClient, APIError


def sso_callback_view(request):
    """
    Empfängt den OTT von sg-gerätemanagement, tauscht ihn gegen
    ein JWT und speichert es in der Session.
    """
    ott = request.GET.get("ott", "").strip()

    if not ott:
        return redirect("/login/?error=sso_missing_token")

    try:
        client = APIClient(base_url=settings.API_BASE_URL)
        response = client.session.post(
            client._url("/api/v1/sso/callback"),
            json={"token": ott},
        )
        data = client._handle_response(response)
        access_token = data.get("access_token")

        if not access_token:
            return redirect("/login/?error=sso_failed")

        # User-Daten laden
        authed_client = APIClient(base_url=settings.API_BASE_URL, token=access_token)
        user_data = authed_client.get_me()

        # Session setzen
        request.session["jwt_token"] = access_token
        request.session["user"] = user_data
        request.session.modified = True

        return redirect("/")

    except APIError:
        return redirect("/login/?error=sso_failed")
    except Exception:
        return redirect("/login/?error=sso_failed")