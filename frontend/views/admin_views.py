"""
Admin views for DHBW Gerätemanagement Frontend.
Device management, user management, and audit logs (Admin only).
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from frontend.decorators import admin_required
from frontend.services.api_client import get_client, APIError


# Valid statuses for the device form
DEVICE_STATUSES = [
    ('verfügbar', 'Verfügbar'),
    ('ausgeliehen', 'Ausgeliehen'),
    ('reserviert', 'Reserviert'),
    ('defekt', 'Defekt'),
    ('außer Betrieb', 'Außer Betrieb'),
]

# Valid roles for the user role form
USER_ROLES = [
    ('Studierende_Mitarbeitende', 'Studierende / Mitarbeitende'),
    ('Administrator', 'Administrator'),
]


# ---------------------------------------------------------------------------
# Admin - Device Management
# ---------------------------------------------------------------------------

@admin_required
def admin_device_list_view(request):
    """Admin device list with all devices and management options."""
    client = get_client(request)
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    context = {
        'current_user': request.current_user,
        'devices': [],
        'status_filter': status_filter,
        'search_query': search_query,
        'statuses': DEVICE_STATUSES,
        'error': None,
    }

    try:
        devices = client.get_devices(
            status=status_filter or None,
            limit=200,
        )
        if search_query:
            q = search_query.lower()
            devices = [
                d for d in devices
                if q in (d.get('name') or '').lower()
                or q in (d.get('inventar_nummer') or '').lower()
                or q in (d.get('hersteller') or '').lower()
                or q in (d.get('modell') or '').lower()
            ]
        context['devices'] = devices
    except APIError as e:
        context['error'] = f'Geräteliste konnte nicht geladen werden: {e.detail}'

    return render(request, 'frontend/admin/devices.html', context)


@admin_required
@require_http_methods(['GET', 'POST'])
def admin_device_create_view(request):
    """Create a new device (Admin)."""
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'statuses': DEVICE_STATUSES,
        'device': None,
        'form_mode': 'create',
        'error': None,
    }

    if request.method == 'POST':
        data = _extract_device_form_data(request.POST)

        try:
            device = client.create_device(data)
            messages.success(request, f'Gerät "{device.get("name")}" erfolgreich angelegt.')
            return redirect('/admin/geraete/')
        except APIError as e:
            if e.status_code == 422:
                messages.error(request, 'Ungültige Eingabe. Bitte überprüfen Sie alle Felder.')
            elif e.status_code == 409:
                messages.error(request, 'Ein Gerät mit dieser Inventarnummer existiert bereits.')
            else:
                messages.error(request, f'Gerät konnte nicht erstellt werden: {e.detail}')
            context['form_data'] = request.POST

    return render(request, 'frontend/admin/device_form.html', context)


@admin_required
@require_http_methods(['GET', 'POST'])
def admin_device_edit_view(request, device_id: int):
    """Edit an existing device (Admin). Only name, standort, status, bemerkungen are editable via PATCH."""
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'statuses': DEVICE_STATUSES,
        'device': None,
        'form_mode': 'edit',
        'error': None,
    }

    try:
        device = client.get_device(device_id)
        context['device'] = device
    except APIError as e:
        context['error'] = f'Gerät konnte nicht geladen werden: {e.detail}'
        return render(request, 'frontend/admin/device_form.html', context)

    if request.method == 'POST':
        # Only PATCH-supported fields per API spec: name, standort, status, bemerkungen
        patch_data = {}
        for field in ('name', 'standort', 'status', 'bemerkungen'):
            val = request.POST.get(field, '').strip()
            if val:
                patch_data[field] = val
            elif field == 'bemerkungen':
                # Allow clearing bemerkungen
                patch_data[field] = request.POST.get(field, '')

        try:
            updated = client.update_device(device_id, patch_data)
            messages.success(request, f'Gerät "{updated.get("name")}" erfolgreich aktualisiert.')
            return redirect('/admin/geraete/')
        except APIError as e:
            if e.status_code == 422:
                messages.error(request, 'Ungültige Eingabe. Bitte überprüfen Sie alle Felder.')
            else:
                messages.error(request, f'Gerät konnte nicht aktualisiert werden: {e.detail}')
            context['form_data'] = request.POST

    return render(request, 'frontend/admin/device_form.html', context)


@admin_required
@require_http_methods(['POST'])
def admin_device_delete_view(request, device_id: int):
    """Delete a device (Admin). POST-only."""
    client = get_client(request)

    try:
        client.delete_device(device_id)
        messages.success(request, 'Gerät erfolgreich gelöscht.')
    except APIError as e:
        if e.status_code == 404:
            messages.error(request, 'Gerät nicht gefunden.')
        elif e.status_code == 409:
            messages.error(request, 'Gerät kann nicht gelöscht werden, da es noch aktive Ausleihen hat.')
        else:
            messages.error(request, f'Gerät konnte nicht gelöscht werden: {e.detail}')

    return redirect('/admin/geraete/')


def _extract_device_form_data(post_data) -> dict:
    """Extract and clean device form data from POST."""
    data = {}
    fields = [
        'inventar_nummer', 'name', 'kategorie', 'hersteller',
        'modell', 'seriennummer', 'standort', 'status',
        'anschaffungsdatum', 'bemerkungen',
    ]
    for field in fields:
        val = post_data.get(field, '').strip()
        if val:
            data[field] = val
    return data


# ---------------------------------------------------------------------------
# Admin - User Management
# ---------------------------------------------------------------------------

@admin_required
def admin_user_list_view(request):
    """Admin user list with role management options."""
    client = get_client(request)
    search_query = request.GET.get('q', '')

    context = {
        'current_user': request.current_user,
        'users': [],
        'search_query': search_query,
        'roles': USER_ROLES,
        'error': None,
    }

    try:
        users = client.get_users(limit=200)
        if search_query:
            q = search_query.lower()
            users = [
                u for u in users
                if q in (u.get('name') or '').lower()
                or q in (u.get('email') or '').lower()
                or q in (u.get('shibboleth_id') or '').lower()
            ]
        context['users'] = users
    except APIError as e:
        context['error'] = f'Benutzerliste konnte nicht geladen werden: {e.detail}'

    return render(request, 'frontend/admin/users.html', context)


@admin_required
@require_http_methods(['POST'])
def admin_user_role_view(request, user_id: int):
    """Update a user's role (Admin). POST-only."""
    client = get_client(request)
    rolle = request.POST.get('rolle', '').strip()

    if rolle not in ('Studierende_Mitarbeitende', 'Administrator'):
        messages.error(request, 'Ungültige Rolle angegeben.')
        return redirect('/admin/benutzer/')

    try:
        user = client.update_user_role(user_id, rolle)
        rolle_display = 'Administrator' if rolle == 'Administrator' else 'Studierende/Mitarbeitende'
        messages.success(
            request,
            f'Rolle von "{user.get("name")}" erfolgreich auf "{rolle_display}" geändert.'
        )
    except APIError as e:
        if e.status_code == 404:
            messages.error(request, 'Benutzer nicht gefunden.')
        else:
            messages.error(request, f'Rollenänderung fehlgeschlagen: {e.detail}')

    return redirect('/admin/benutzer/')


@admin_required
@require_http_methods(['POST'])
def admin_user_delete_view(request, user_id: int):
    """Delete a user (Admin). POST-only."""
    client = get_client(request)

    # Prevent self-deletion
    current_user = request.current_user
    if current_user and str(current_user.get('id')) == str(user_id):
        messages.error(request, 'Sie können Ihr eigenes Konto nicht löschen.')
        return redirect('/admin/benutzer/')

    try:
        client.delete_user(user_id)
        messages.success(request, 'Benutzer erfolgreich gelöscht.')
    except APIError as e:
        if e.status_code == 404:
            messages.error(request, 'Benutzer nicht gefunden.')
        else:
            messages.error(request, f'Benutzer konnte nicht gelöscht werden: {e.detail}')

    return redirect('/admin/benutzer/')


# ---------------------------------------------------------------------------
# Admin - Audit Logs
# ---------------------------------------------------------------------------

@admin_required
def admin_audit_logs_view(request):
    """Global audit log listing (Admin)."""
    client = get_client(request)
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1

    limit = 50
    skip = (page - 1) * limit

    context = {
        'current_user': request.current_user,
        'logs': [],
        'page': page,
        'has_next': False,
        'has_prev': page > 1,
        'error': None,
    }

    try:
        logs = client.get_audit_logs(skip=skip, limit=limit + 1)
        context['has_next'] = len(logs) > limit
        context['logs'] = logs[:limit]
    except APIError as e:
        context['error'] = f'Audit-Logs konnten nicht geladen werden: {e.detail}'

    return render(request, 'frontend/admin/audit_logs.html', context)


@admin_required
def admin_device_audit_logs_view(request, device_id: int):
    """Audit logs for a specific device (Admin)."""
    client = get_client(request)

    context = {
        'current_user': request.current_user,
        'logs': [],
        'device': None,
        'error': None,
    }

    try:
        device = client.get_device(device_id)
        context['device'] = device
    except APIError:
        pass

    try:
        logs = client.get_device_audit_logs(device_id, limit=200)
        context['logs'] = logs
    except APIError as e:
        context['error'] = f'Audit-Logs konnten nicht geladen werden: {e.detail}'

    return render(request, 'frontend/admin/audit_logs.html', context)
