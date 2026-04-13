"""
Custom template tags and filters for DHBW Gerätemanagement Frontend.
Provides status badges, date formatting, and other helpers.
"""

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


# ---------------------------------------------------------------------------
# Status Badge Filters
# ---------------------------------------------------------------------------

# Map GeraeteStatus values to badge CSS classes
GERAET_STATUS_CLASSES = {
    'verfügbar': 'badge-ok',
    'ausgeliehen': 'badge-warn',
    'reserviert': 'badge-neutral',
    'defekt': 'badge-danger',
    'außer Betrieb': 'badge-danger',
}

GERAET_STATUS_LABELS = {
    'verfügbar': 'Verfügbar',
    'ausgeliehen': 'Ausgeliehen',
    'reserviert': 'Reserviert',
    'defekt': 'Defekt',
    'außer Betrieb': 'Außer Betrieb',
}

# Map AusleihStatus values to badge CSS classes
AUSLEIHE_STATUS_CLASSES = {
    'aktiv': 'badge-ok',
    'überfällig': 'badge-danger',
    'abgeschlossen': 'badge-neutral',
}

AUSLEIHE_STATUS_LABELS = {
    'aktiv': 'Aktiv',
    'überfällig': 'Überfällig',
    'abgeschlossen': 'Abgeschlossen',
}

# Map ReservierungsStatus values to badge CSS classes
RESERVIERUNG_STATUS_CLASSES = {
    'aktiv': 'badge-ok',
    'erfüllt': 'badge-neutral',
    'storniert': 'badge-danger',
}

RESERVIERUNG_STATUS_LABELS = {
    'aktiv': 'Aktiv',
    'erfüllt': 'Erfüllt',
    'storniert': 'Storniert',
}

# Map BenutzerRolle values
BENUTZER_ROLLE_LABELS = {
    'Studierende_Mitarbeitende': 'Studierende/Mitarbeitende',
    'Administrator': 'Administrator',
}

# Map AktionType values
AKTION_LABELS = {
    'angelegt': 'Angelegt',
    'bearbeitet': 'Bearbeitet',
    'status_änderung': 'Statusänderung',
    'ausleihe': 'Ausleihe',
    'verlängerung': 'Verlängerung',
    'rückgabe': 'Rückgabe',
    'reservierung': 'Reservierung',
}


@register.filter(name='geraet_status_badge')
def geraet_status_badge(status: str) -> str:
    """
    Returns an HTML badge span for a GeraeteStatus value.
    Usage: {{ device.status|geraet_status_badge }}
    """
    css_class = GERAET_STATUS_CLASSES.get(status, 'badge-neutral')
    label = GERAET_STATUS_LABELS.get(status, status)
    return format_html('<span class="badge {}">{}</span>', css_class, label)


@register.filter(name='ausleihe_status_badge')
def ausleihe_status_badge(status: str) -> str:
    """
    Returns an HTML badge span for an AusleihStatus value.
    Usage: {{ loan.status|ausleihe_status_badge }}
    """
    css_class = AUSLEIHE_STATUS_CLASSES.get(status, 'badge-neutral')
    label = AUSLEIHE_STATUS_LABELS.get(status, status)
    return format_html('<span class="badge {}">{}</span>', css_class, label)


@register.filter(name='reservierung_status_badge')
def reservierung_status_badge(status: str) -> str:
    """
    Returns an HTML badge span for a ReservierungsStatus value.
    Usage: {{ reservation.status|reservierung_status_badge }}
    """
    css_class = RESERVIERUNG_STATUS_CLASSES.get(status, 'badge-neutral')
    label = RESERVIERUNG_STATUS_LABELS.get(status, status)
    return format_html('<span class="badge {}">{}</span>', css_class, label)


@register.filter(name='rolle_label')
def rolle_label(rolle: str) -> str:
    """
    Returns German label for a BenutzerRolle value.
    Usage: {{ user.rolle|rolle_label }}
    """
    return BENUTZER_ROLLE_LABELS.get(rolle, rolle)


@register.filter(name='aktion_label')
def aktion_label(aktion: str) -> str:
    """
    Returns German label for an AktionType value.
    Usage: {{ log.aktion|aktion_label }}
    """
    return AKTION_LABELS.get(aktion, aktion)


@register.filter(name='format_date')
def format_date(value: str) -> str:
    """
    Format an ISO date string (YYYY-MM-DD or ISO datetime) to German format (DD.MM.YYYY).
    Usage: {{ device.anschaffungsdatum|format_date }}
    """
    if not value:
        return '–'
    try:
        from datetime import datetime
        # Handle ISO datetime strings
        if 'T' in str(value):
            dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(str(value)[:10], '%Y-%m-%d')
        return dt.strftime('%d.%m.%Y')
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='format_datetime')
def format_datetime(value: str) -> str:
    """
    Format an ISO datetime string to German format (DD.MM.YYYY HH:MM).
    Usage: {{ log.zeitstempel|format_datetime }}
    """
    if not value:
        return '–'
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='geraet_status_class')
def geraet_status_class(status: str) -> str:
    """Returns CSS class for a GeraeteStatus (without HTML). For use in class attributes."""
    return GERAET_STATUS_CLASSES.get(status, 'badge-neutral')


@register.simple_tag
def is_admin(user) -> bool:
    """Returns True if the user dict has rolle == 'Administrator'."""
    if not user:
        return False
    return user.get('rolle') == 'Administrator'


@register.filter(name='can_extend')
def can_extend(loan) -> bool:
    """Returns True if a loan can still be extended (verlaengerungen_anzahl < 2)."""
    if not loan:
        return False
    return (
        loan.get('status') in ('aktiv', 'überfällig')
        and int(loan.get('verlaengerungen_anzahl', 0)) < 2
    )


@register.filter(name='default_dash')
def default_dash(value) -> str:
    """Returns '–' if value is falsy, otherwise the value itself."""
    return value if value else '–'
