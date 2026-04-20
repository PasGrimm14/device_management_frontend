"""
Dashboard view for DHBW Gerätemanagement Frontend.
"""

from django.shortcuts import render

from frontend.decorators import login_required
from frontend.services.api_client import get_client, APIError


@login_required
def dashboard_view(request):
    client = get_client(request)
    is_admin = request.current_user and request.current_user.get('rolle') == 'Administrator'

    context = {
        'current_user': request.current_user,
        'is_admin': is_admin,
        # Globale Gerätezahlen (alle Nutzer)
        'stats': {
            'verfuegbar': 0,
            'ausgeliehen': 0,
            'reserviert': 0,
            'defekt': 0,
            'ausser_betrieb': 0,
        },
        # Persönliche Zahlen (eigene Ausleihen/Reservierungen)
        'my_stats': {
            'meine_ausleihen': 0,
            'meine_reservierungen': 0,
            'meine_ueberfaellig': 0,
        },
        # Admin-Zahlen (systemweit)
        'admin_stats': {
            'aktive_ausleihen': 0,
            'aktive_reservierungen': 0,
            'gesamt_ueberfaellig': 0,
        },
        'active_loans': [],
        'recent_devices': [],
        'error': None,
    }

    # ── Gerätestatus (alle Nutzer sehen verfügbare Geräte) ───────────────────
    try:
        devices = client.get_devices(limit=200)
        stats = context['stats']
        for device in devices:
            s = device.get('status', '')
            if s == 'verfügbar':        stats['verfuegbar'] += 1
            elif s == 'ausgeliehen':    stats['ausgeliehen'] += 1
            elif s == 'reserviert':     stats['reserviert'] += 1
            elif s == 'defekt':         stats['defekt'] += 1
            elif s == 'außer Betrieb':  stats['ausser_betrieb'] += 1
        context['recent_devices'] = devices[:6]
    except APIError as e:
        context['error'] = f'Geräte konnten nicht geladen werden: {e.detail}'

    # ── Eigene Ausleihen ─────────────────────────────────────────────────────
    try:
        loans = client.get_loans(limit=200)
        current_user_id = request.current_user.get('id') if request.current_user else None
        if is_admin:
            loans = [l for l in loans if l.get('nutzer_id') == current_user_id]
        active = [l for l in loans if l.get('status') in ('aktiv', 'überfällig')]
        overdue = [l for l in loans if l.get('status') == 'überfällig']
        context['active_loans'] = active[:5]
        context['my_stats']['meine_ausleihen'] = len(active)
        context['my_stats']['meine_ueberfaellig'] = len(overdue)
    except APIError:
        pass

    # ── Eigene Reservierungen ────────────────────────────────────────────────
    try:
        reservations = client.get_reservations(limit=200)
        current_user_id = request.current_user.get('id') if request.current_user else None
        if is_admin:
            reservations = [r for r in reservations if r.get('nutzer_id') == current_user_id]
        aktive_res = [r for r in reservations if r.get('status') == 'aktiv']
        context['my_stats']['meine_reservierungen'] = len(aktive_res)
    except APIError:
        pass

    # ── Admin: systemweite Zahlen ────────────────────────────────────────────
    if is_admin:
        try:
            statistik = client.get_statistik()
            context['admin_stats']['aktive_ausleihen']    = statistik.get('ausleihen_aktiv', 0)
            context['admin_stats']['gesamt_ueberfaellig'] = statistik.get('ausleihen_ueberfaellig', 0)
            # Reservierungen: aus Gerätestatus ableiten
            context['admin_stats']['aktive_reservierungen'] = context['stats']['reserviert']
        except APIError:
            pass

    return render(request, 'frontend/dashboard.html', context)
