"""
Dashboard view for DHBW Gerätemanagement Frontend.
Computes stats from API data and displays them.
"""

from django.shortcuts import render
from django.contrib import messages

from frontend.decorators import login_required
from frontend.services.api_client import get_client, APIError


@login_required
def dashboard_view(request):
    """
    Main dashboard page.
    Shows stats: available devices, active loans, reservations, overdue loans.
    Also shows recent loans and available device list.
    """
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'stats': {
            'verfuegbar': 0,
            'ausgeliehen': 0,
            'reserviert': 0,
            'defekt': 0,
        },
        'active_loans': [],
        'recent_devices': [],
        'overdue_count': 0,
        'error': None,
    }

    try:
        # Fetch all devices for stats
        devices = client.get_devices(limit=200)
        stats = {'verfuegbar': 0, 'ausgeliehen': 0, 'reserviert': 0, 'defekt': 0, 'ausser_betrieb': 0}
        for device in devices:
            status = device.get('status', '')
            if status == 'verfügbar':
                stats['verfuegbar'] += 1
            elif status == 'ausgeliehen':
                stats['ausgeliehen'] += 1
            elif status == 'reserviert':
                stats['reserviert'] += 1
            elif status == 'defekt':
                stats['defekt'] += 1
            elif status == 'außer Betrieb':
                stats['ausser_betrieb'] += 1

        context['stats'] = stats
        context['recent_devices'] = devices[:6]

    except APIError as e:
        context['error'] = f'Geräte konnten nicht geladen werden: {e.detail}'

    try:
        # Fetch loans for current user
        loans = client.get_loans(limit=50)
        active_loans = [l for l in loans if l.get('status') in ('aktiv', 'überfällig')]
        overdue_loans = [l for l in loans if l.get('status') == 'überfällig']

        context['active_loans'] = active_loans[:5]
        context['overdue_count'] = len(overdue_loans)

    except APIError as e:
        # Non-fatal: just show empty loans
        pass

    return render(request, 'frontend/dashboard.html', context)
