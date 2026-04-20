"""
Custom template tags and filters for DHBW Gerätemanagement Frontend.
"""

from django import template
from django.utils.html import format_html

register = template.Library()

GERAET_STATUS_CLASSES = {
    'verfügbar': 'badge-ok',
    'ausgeliehen': 'badge-warn',
    'reserviert': 'badge-neutral',
    'defekt': 'badge-danger',
    'außer Betrieb': 'badge-danger',
    'zur Zeit nicht vorhanden': 'badge-neutral',
}

GERAET_STATUS_LABELS = {
    'verfügbar': 'Verfügbar',
    'ausgeliehen': 'Ausgeliehen',
    'reserviert': 'Reserviert',
    'defekt': 'Defekt',
    'außer Betrieb': 'Außer Betrieb',
    'zur Zeit nicht vorhanden': 'Zur Zeit nicht vorhanden',
}

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

BENUTZER_ROLLE_LABELS = {
    'Studierende_Mitarbeitende': 'Studierende/Mitarbeitende',
    'Administrator': 'Administrator',
}

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
    css_class = GERAET_STATUS_CLASSES.get(status, 'badge-neutral')
    label = GERAET_STATUS_LABELS.get(status, status)
    return format_html('<span class="badge {}">{}</span>', css_class, label)


@register.filter(name='ausleihe_status_badge')
def ausleihe_status_badge(status: str) -> str:
    css_class = AUSLEIHE_STATUS_CLASSES.get(status, 'badge-neutral')
    label = AUSLEIHE_STATUS_LABELS.get(status, status)
    return format_html('<span class="badge {}">{}</span>', css_class, label)


@register.filter(name='reservierung_status_badge')
def reservierung_status_badge(status: str) -> str:
    css_class = RESERVIERUNG_STATUS_CLASSES.get(status, 'badge-neutral')
    label = RESERVIERUNG_STATUS_LABELS.get(status, status)
    return format_html('<span class="badge {}">{}</span>', css_class, label)


@register.filter(name='rolle_label')
def rolle_label(rolle: str) -> str:
    return BENUTZER_ROLLE_LABELS.get(rolle, rolle)


@register.filter(name='aktion_label')
def aktion_label(aktion: str) -> str:
    return AKTION_LABELS.get(aktion, aktion)


@register.filter(name='format_date')
def format_date(value: str) -> str:
    if not value:
        return '–'
    try:
        from datetime import datetime
        if 'T' in str(value):
            dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(str(value)[:10], '%Y-%m-%d')
        return dt.strftime('%d.%m.%Y')
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='format_datetime')
def format_datetime(value: str) -> str:
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
    return GERAET_STATUS_CLASSES.get(status, 'badge-neutral')


@register.simple_tag
def is_admin(user) -> bool:
    if not user:
        return False
    return user.get('rolle') == 'Administrator'


@register.filter(name='can_extend')
def can_extend(loan) -> bool:
    if not loan:
        return False
    return (
        loan.get('status') in ('aktiv', 'überfällig')
        and int(loan.get('verlaengerungen_anzahl', 0)) < 2
    )


@register.filter(name='can_extend_langzeit')
def can_extend_langzeit(loan) -> bool:
    """Zeigt die Langzeit-Option an, wenn Gerät das Flag hat und es noch nicht genutzt wurde."""
    if not loan:
        return False
    geraet = loan.get('geraet') or {}
    langzeit_aktiv = geraet.get('langzeit_ausleihe', False)
    bereits_genutzt = loan.get('langzeit_verlaengerung_genutzt', False)
    status_ok = loan.get('status') in ('aktiv', 'überfällig')
    return langzeit_aktiv and not bereits_genutzt and status_ok


@register.filter(name='default_dash')
def default_dash(value) -> str:
    return value if value else '–'
