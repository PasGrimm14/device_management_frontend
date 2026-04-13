"""
Device views for DHBW Gerätemanagement Frontend.
Device list and device detail pages.
"""

from django.shortcuts import render, redirect
from django.contrib import messages

from frontend.decorators import login_required
from frontend.services.api_client import get_client, APIError


# Available device statuses for filter dropdown
DEVICE_STATUSES = [
    ('', 'Alle Status'),
    ('verfügbar', 'Verfügbar'),
    ('ausgeliehen', 'Ausgeliehen'),
    ('reserviert', 'Reserviert'),
    ('defekt', 'Defekt'),
    ('außer Betrieb', 'Außer Betrieb'),
]


@login_required
def device_list_view(request):
    """
    Device list page with optional status/category filter.
    Displays devices in a card grid.
    """
    client = get_client(request)

    status_filter = request.GET.get('status', '')
    kategorie_filter = request.GET.get('kategorie', '')
    search_query = request.GET.get('q', '')

    context = {
        'current_user': request.current_user,
        'devices': [],
        'status_filter': status_filter,
        'kategorie_filter': kategorie_filter,
        'search_query': search_query,
        'statuses': DEVICE_STATUSES,
        'kategorien': [],
        'error': None,
    }

    try:
        devices = client.get_devices(
            status=status_filter or None,
            kategorie=kategorie_filter or None,
            limit=200,
        )

        # Client-side search filter (API may not support text search)
        if search_query:
            q = search_query.lower()
            devices = [
                d for d in devices
                if q in (d.get('name') or '').lower()
                or q in (d.get('hersteller') or '').lower()
                or q in (d.get('modell') or '').lower()
                or q in (d.get('inventar_nummer') or '').lower()
            ]

        # Extract unique categories for filter dropdown
        kategorien = sorted(set(
            d.get('kategorie') for d in devices if d.get('kategorie')
        ))
        context['devices'] = devices
        context['kategorien'] = kategorien

    except APIError as e:
        context['error'] = f'Geräteliste konnte nicht geladen werden: {e.detail}'

    return render(request, 'frontend/devices.html', context)


@login_required
def device_detail_view(request, device_id: int):
    """
    Device detail page.
    Shows full device info, active loans/reservations.
    """
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'device': None,
        'active_loan': None,
        'active_reservation': None,
        'error': None,
    }

    try:
        device = client.get_device(device_id)
        context['device'] = device
    except APIError as e:
        if e.status_code == 404:
            context['error'] = 'Gerät nicht gefunden.'
        else:
            context['error'] = f'Gerät konnte nicht geladen werden: {e.detail}'
        return render(request, 'frontend/device_detail.html', context)

    # Check if user has active loan for this device
    try:
        loans = client.get_loans(limit=100)
        for loan in loans:
            if (loan.get('geraet_id') == device_id
                    and loan.get('status') in ('aktiv', 'überfällig')):
                context['active_loan'] = loan
                break
    except APIError:
        pass

    # Check active reservation for this device
    try:
        reservations = client.get_reservations(limit=100)
        for res in reservations:
            if (res.get('geraet_id') == device_id
                    and res.get('status') == 'aktiv'):
                context['active_reservation'] = res
                break
    except APIError:
        pass

    return render(request, 'frontend/device_detail.html', context)
