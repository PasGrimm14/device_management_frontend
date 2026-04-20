"""
Loan views for DHBW Gerätemanagement Frontend.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from frontend.decorators import login_required
from frontend.services.api_client import get_client, APIError


@login_required
def loan_list_view(request):
    client = get_client(request)
    status_filter = request.GET.get('status', '')
    context = {
        'current_user': request.current_user,
        'loans': [],
        'status_filter': status_filter,
        'error': None,
    }
    try:
        loans = client.get_loans(limit=200)
        loans.sort(key=lambda l: l.get('geplantes_rueckgabedatum') or '')
        if status_filter:
            loans = [l for l in loans if l.get('status') == status_filter]
        context['loans'] = loans
    except APIError as e:
        context['error'] = f'Ausleihliste konnte nicht geladen werden: {e.detail}'
    return render(request, 'frontend/loans.html', context)


@login_required
def loan_detail_view(request, loan_id: int):
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'loan': None,
        'error': None,
    }
    try:
        loan = client.get_loan(loan_id)
        context['loan'] = loan
    except APIError as e:
        if e.status_code == 404:
            context['error'] = 'Ausleihe nicht gefunden.'
        else:
            context['error'] = f'Ausleihe konnte nicht geladen werden: {e.detail}'
    return render(request, 'frontend/loan_detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def loan_create_view(request, device_id: int):
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'device': None,
        'error': None,
    }
    try:
        device = client.get_device(device_id)
        context['device'] = device
        if device.get('status') != 'verfügbar':
            messages.warning(
                request,
                f'Das Gerät "{device.get("name")}" ist derzeit nicht verfügbar '
                f'(Status: {device.get("status")}).'
            )
    except APIError as e:
        context['error'] = f'Gerät konnte nicht geladen werden: {e.detail}'
        return render(request, 'frontend/loan_request.html', context)

    if request.method == 'POST':
        geplantes_rueckgabedatum = request.POST.get('geplantes_rueckgabedatum', '').strip() or None
        try:
            loan = client.create_loan(geraet_id=device_id, geplantes_rueckgabedatum=geplantes_rueckgabedatum)
            messages.success(
                request,
                f'Ausleihe erfolgreich erstellt! '
                f'Rückgabe bis: {loan.get("geplantes_rueckgabedatum", "nicht angegeben")}.'
            )
            return redirect(f'/ausleihen/{loan["id"]}/')
        except APIError as e:
            if e.status_code == 409:
                messages.error(request, 'Das Gerät ist bereits ausgeliehen.')
            elif e.status_code == 422:
                messages.error(request, 'Ungültige Eingabe. Bitte überprüfen Sie das Rückgabedatum.')
            else:
                messages.error(request, f'Ausleihe konnte nicht erstellt werden: {e.detail}')

    return render(request, 'frontend/loan_request.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def loan_extend_view(request, loan_id: int):
    client = get_client(request)
    context = {
        'current_user': request.current_user,
        'loan': None,
        'error': None,
    }
    try:
        loan = client.get_loan(loan_id)
        context['loan'] = loan
    except APIError as e:
        context['error'] = f'Ausleihe konnte nicht geladen werden: {e.detail}'
        return render(request, 'frontend/loan_extend.html', context)

    if request.method == 'POST':
        langzeit = request.POST.get('langzeit') == '1'
        try:
            updated_loan = client.extend_loan(loan_id, langzeit=langzeit)
            if langzeit:
                msg = f'Langzeit-Verlängerung erfolgreich! Neues Rückgabedatum: {updated_loan.get("geplantes_rueckgabedatum", "unbekannt")}.'
            else:
                msg = f'Ausleihe erfolgreich verlängert! Neues Rückgabedatum: {updated_loan.get("geplantes_rueckgabedatum", "unbekannt")}.'
            messages.success(request, msg)
            return redirect(f'/ausleihen/{loan_id}/')
        except APIError as e:
            if e.status_code == 400:
                messages.error(request, 'Maximale Anzahl an Verlängerungen bereits erreicht.')
            elif e.status_code == 403:
                messages.error(request, 'Sie sind nicht berechtigt, diese Ausleihe zu verlängern.')
            elif e.status_code == 404:
                messages.error(request, 'Ausleihe nicht gefunden.')
            elif e.status_code == 409:
                messages.error(request, e.detail)
            else:
                messages.error(request, f'Verlängerung fehlgeschlagen: {e.detail}')

    return render(request, 'frontend/loan_extend.html', context)


@login_required
@require_http_methods(['POST'])
def loan_return_view(request, loan_id: int):
    client = get_client(request)
    zustand = request.POST.get('zustand', '').strip() or None
    try:
        client.return_loan_with_condition(loan_id, zustand=zustand)
        messages.success(request, 'Gerät erfolgreich zurückgegeben.')
    except APIError as e:
        if e.status_code == 400:
            messages.error(request, 'Diese Ausleihe wurde bereits abgeschlossen.')
        elif e.status_code == 403:
            messages.error(request, 'Sie sind nicht berechtigt, diese Rückgabe durchzuführen.')
        elif e.status_code == 404:
            messages.error(request, 'Ausleihe nicht gefunden.')
        else:
            messages.error(request, f'Rückgabe fehlgeschlagen: {e.detail}')
    return redirect('/ausleihen/')
