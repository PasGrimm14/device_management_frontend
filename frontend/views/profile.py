"""
Profile, help, and scanner views for DHBW Gerätemanagement Frontend.
"""

from django.shortcuts import render
from django.contrib import messages

from frontend.decorators import login_required
from frontend.services.api_client import get_client, APIError


@login_required
def profile_view(request):
    """
    User profile page.
    Shows user info from session and fetches fresh data from API.
    Also shows user's loan and reservation history.
    """
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'profile': request.current_user,
        'loans': [],
        'reservations': [],
        'error': None,
    }

    # Fetch fresh profile data
    try:
        profile = client.get_me()
        context['profile'] = profile
        # Update session with fresh data
        request.session['user'] = profile
        request.session.modified = True
    except APIError as e:
        context['error'] = f'Profil konnte nicht geladen werden: {e.detail}'

    # Fetch user's loans
    try:
        loans = client.get_loans(limit=100)
        context['loans'] = loans
    except APIError:
        pass

    # Fetch user's reservations
    try:
        reservations = client.get_reservations(limit=100)
        context['reservations'] = reservations
    except APIError:
        pass

    return render(request, 'frontend/profile.html', context)


@login_required
def help_view(request):
    """Help page with FAQ and usage instructions."""
    return render(request, 'frontend/help.html', {
        'current_user': request.current_user,
    })


@login_required
def scanner_view(request):
    """
    QR code scanner page.
    Uses the device camera to scan QR codes and redirect to device detail.
    """
    return render(request, 'frontend/scanner.html', {
        'current_user': request.current_user,
    })
