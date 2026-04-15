"""
Standort-Verwaltung für DHBW Gerätemanagement Frontend.
Bildungseinrichtungen, Standorte und Boxen (Admin only).
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from frontend.decorators import admin_required
from frontend.services.api_client import get_client, APIError


@admin_required
def admin_standort_list_view(request):
    """Übersicht: Bildungseinrichtungen → Standorte → Boxen."""
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'einrichtungen': [],
        'standorte': [],
        'boxen': [],
        'error': None,
    }

    try:
        context['einrichtungen'] = client.get_bildungseinrichtungen(limit=200)
    except APIError as e:
        context['error'] = f'Bildungseinrichtungen konnten nicht geladen werden: {e.detail}'

    try:
        context['standorte'] = client.get_standorte(limit=500)
    except APIError:
        pass

    try:
        context['boxen'] = client.get_boxes(limit=500)
    except APIError:
        pass

    return render(request, 'frontend/admin/standorte.html', context)


@admin_required
@require_http_methods(['GET', 'POST'])
def admin_bildungseinrichtung_create_view(request):
    """Neue Bildungseinrichtung anlegen."""
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'form_type': 'einrichtung',
        'form_data': {},
        'error': None,
    }

    if request.method == 'POST':
        data = {}
        for field in ('name', 'strasse', 'hausnummer', 'plz', 'ort', 'bundesland'):
            val = request.POST.get(field, '').strip()
            if val:
                data[field] = val

        try:
            client.create_bildungseinrichtung(data)
            messages.success(request, f'Bildungseinrichtung "{data.get("name")}" erfolgreich angelegt.')
            return redirect('/admin/standorte/')
        except APIError as e:
            if e.status_code == 422:
                messages.error(request, 'Ungültige Eingabe. Bitte überprüfen Sie alle Felder.')
            else:
                messages.error(request, f'Bildungseinrichtung konnte nicht angelegt werden: {e.detail}')
            context['form_data'] = request.POST

    return render(request, 'frontend/admin/standort_form.html', context)


@admin_required
@require_http_methods(['GET', 'POST'])
def admin_standort_create_view(request):
    """Neuen Standort anlegen."""
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'form_type': 'standort',
        'form_data': {},
        'einrichtungen': [],
        'error': None,
    }

    try:
        context['einrichtungen'] = client.get_bildungseinrichtungen(limit=200)
    except APIError as e:
        context['error'] = f'Bildungseinrichtungen konnten nicht geladen werden: {e.detail}'

    if request.method == 'POST':
        data = {}
        for field in ('gebaeude', 'raum', 'beschreibung'):
            val = request.POST.get(field, '').strip()
            if val:
                data[field] = val
        einrichtung_id = request.POST.get('bildungseinrichtung_id', '').strip()
        if einrichtung_id:
            try:
                data['bildungseinrichtung_id'] = int(einrichtung_id)
            except ValueError:
                pass

        try:
            client.create_standort(data)
            messages.success(request, 'Standort erfolgreich angelegt.')
            return redirect('/admin/standorte/')
        except APIError as e:
            if e.status_code == 422:
                messages.error(request, 'Ungültige Eingabe. Bitte überprüfen Sie alle Felder.')
            else:
                messages.error(request, f'Standort konnte nicht angelegt werden: {e.detail}')
            context['form_data'] = request.POST

    return render(request, 'frontend/admin/standort_form.html', context)


@admin_required
@require_http_methods(['GET', 'POST'])
def admin_box_create_view(request):
    """Neue Box anlegen."""
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'form_type': 'box',
        'form_data': {},
        'standorte': [],
        'error': None,
    }

    try:
        context['standorte'] = client.get_standorte(limit=500)
    except APIError as e:
        context['error'] = f'Standorte konnten nicht geladen werden: {e.detail}'

    if request.method == 'POST':
        data = {}
        for field in ('box_nummer', 'beschreibung'):
            val = request.POST.get(field, '').strip()
            if val:
                data[field] = val
        standort_id = request.POST.get('standort_id', '').strip()
        if standort_id:
            try:
                data['standort_id'] = int(standort_id)
            except ValueError:
                pass

        try:
            client.create_box(data)
            messages.success(request, f'Box "{data.get("box_nummer")}" erfolgreich angelegt.')
            return redirect('/admin/standorte/')
        except APIError as e:
            if e.status_code == 422:
                messages.error(request, 'Ungültige Eingabe. Bitte überprüfen Sie alle Felder.')
            else:
                messages.error(request, f'Box konnte nicht angelegt werden: {e.detail}')
            context['form_data'] = request.POST

    return render(request, 'frontend/admin/standort_form.html', context)
