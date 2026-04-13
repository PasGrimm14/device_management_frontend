"""
Reservation views for DHBW Gerätemanagement Frontend.
List, create, and cancel reservations.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from frontend.decorators import login_required
from frontend.services.api_client import get_client, APIError


@login_required
def reservation_list_view(request):
    """
    Reservation list page.
    Shows all active reservations for the current user.
    """
    client = get_client(request)
    status_filter = request.GET.get('status', '')

    context = {
        'current_user': request.current_user,
        'reservations': [],
        'status_filter': status_filter,
        'error': None,
    }

    try:
        reservations = client.get_reservations(limit=200)
        if status_filter:
            reservations = [r for r in reservations if r.get('status') == status_filter]
        context['reservations'] = reservations
    except APIError as e:
        context['error'] = f'Reservierungsliste konnte nicht geladen werden: {e.detail}'

    return render(request, 'frontend/reservations.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def reservation_create_view(request, device_id: int):
    """
    Create a reservation for a specific device.
    Form collects reserviert_fuer_datum; geraet_id comes from URL.
    Accessible from device detail page.
    """
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'device': None,
        'error': None,
    }

    # Load device info for display
    try:
        device = client.get_device(device_id)
        context['device'] = device
    except APIError as e:
        context['error'] = f'Gerät konnte nicht geladen werden: {e.detail}'
        return render(request, 'frontend/reservation_create.html', context)

    if request.method == 'POST':
        reserviert_fuer_datum = request.POST.get('reserviert_fuer_datum', '').strip()

        if not reserviert_fuer_datum:
            messages.error(request, 'Bitte wählen Sie ein Reservierungsdatum aus.')
            return render(request, 'frontend/reservation_create.html', context)

        try:
            reservation = client.create_reservation(
                geraet_id=device_id,
                reserviert_fuer_datum=reserviert_fuer_datum,
            )
            messages.success(
                request,
                f'Reservierung erfolgreich erstellt für den '
                f'{reservation.get("reserviert_fuer_datum", reserviert_fuer_datum)}.'
            )
            return redirect('/reservierungen/')
        except APIError as e:
            if e.status_code == 409:
                messages.error(request, 'Das Gerät ist für dieses Datum bereits reserviert.')
            elif e.status_code == 422:
                messages.error(request, 'Ungültiges Datum. Bitte wählen Sie ein zukünftiges Datum.')
            else:
                messages.error(request, f'Reservierung konnte nicht erstellt werden: {e.detail}')

    return render(request, 'frontend/reservation_create.html', context)


@login_required
@require_http_methods(['POST'])
def reservation_cancel_view(request, reservation_id: int):
    """
    Cancel a reservation. POST-only action.
    Redirects to reservation list on completion.
    """
    client = get_client(request)

    try:
        client.cancel_reservation(reservation_id)
        messages.success(request, 'Reservierung erfolgreich storniert.')
    except APIError as e:
        if e.status_code == 403:
            messages.error(request, 'Sie sind nicht berechtigt, diese Reservierung zu stornieren.')
        elif e.status_code == 404:
            messages.error(request, 'Reservierung nicht gefunden.')
        else:
            messages.error(request, f'Stornierung fehlgeschlagen: {e.detail}')

    return redirect('/reservierungen/')
