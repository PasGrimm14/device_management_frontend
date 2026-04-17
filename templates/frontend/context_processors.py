from django.conf import settings


def api_base_url(request):
    """Stellt API_BASE_URL in allen Templates zur Verfügung."""
    return {'API_BASE_URL': settings.API_BASE_URL}