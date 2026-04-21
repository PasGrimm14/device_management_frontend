"""
Central API client for DHBW Gerätemanagement Frontend.
Handles all communication with the backend REST API.
"""

import requests
from django.conf import settings


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


class APIClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> dict | list:
        if response.status_code >= 400:
            try:
                detail = response.json().get('detail', response.text)
            except Exception:
                detail = response.text or f"HTTP {response.status_code}"
            raise APIError(response.status_code, str(detail))
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    # -------------------------------------------------------------------------
    # Auth
    # -------------------------------------------------------------------------

    def login(self, shibboleth_id: str, name: str, email: str) -> dict:
        response = self.session.post(
            self._url('/api/v1/auth/token'),
            json={'shibboleth_id': shibboleth_id, 'name': name, 'email': email},
        )
        return self._handle_response(response)

    # -------------------------------------------------------------------------
    # Geräte (Devices)
    # -------------------------------------------------------------------------

    def get_devices(self, status=None, kategorie=None, q=None, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        if status: params['status'] = status
        if kategorie: params['kategorie'] = kategorie
        if q: params['q'] = q
        response = self.session.get(self._url('/api/v1/geraete/'), params=params)
        return self._handle_response(response)

    def get_device(self, device_id: int) -> dict:
        response = self.session.get(self._url(f'/api/v1/geraete/{device_id}'))
        return self._handle_response(response)

    def create_device(self, data: dict) -> dict:
        response = self.session.post(self._url('/api/v1/geraete/'), json=data)
        return self._handle_response(response)

    def update_device(self, device_id: int, data: dict) -> dict:
        response = self.session.patch(self._url(f'/api/v1/geraete/{device_id}'), json=data)
        return self._handle_response(response)

    def delete_device(self, device_id: int) -> dict:
        response = self.session.delete(self._url(f'/api/v1/geraete/{device_id}'))
        return self._handle_response(response)

    def get_qr_code(self, device_id: int) -> requests.Response:
        return self.session.get(self._url(f'/api/v1/geraete/{device_id}/qr-code'))

    def upload_device_image(self, file_content: bytes, filename: str, mime_type: str) -> dict:
        response = self.session.post(
            self._url('/api/v1/admin/bilder'),
            files={'datei': (filename, file_content, mime_type)},
        )
        return self._handle_response(response)

    def assign_device_image(self, device_id: int, bild_id: int) -> dict:
        response = self.session.put(
            self._url(f'/api/v1/admin/geraete/{device_id}/bild'),
            json={'bild_id': bild_id},
        )
        return self._handle_response(response)

    def get_device_image_url(self, device_id: int) -> requests.Response:
        return self.session.get(self._url(f'/api/v1/geraete/{device_id}/bild'))

    # -------------------------------------------------------------------------
    # Ausleihen (Loans)
    # -------------------------------------------------------------------------

    def get_loans(self, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(self._url('/api/v1/ausleihen/'), params=params)
        return self._handle_response(response)

    def get_loan(self, loan_id: int) -> dict:
        response = self.session.get(self._url(f'/api/v1/ausleihen/{loan_id}'))
        return self._handle_response(response)

    def create_loan(self, geraet_id: int, geplantes_rueckgabedatum=None) -> dict:
        data: dict = {'geraet_id': geraet_id}
        if geplantes_rueckgabedatum:
            data['geplantes_rueckgabedatum'] = geplantes_rueckgabedatum
        response = self.session.post(self._url('/api/v1/ausleihen/'), json=data)
        return self._handle_response(response)

    def extend_loan(self, loan_id: int, langzeit: bool = False) -> dict:
        """Verlängert eine Ausleihe. Bei langzeit=True: 80-Tage-Verlängerung."""
        response = self.session.post(
            self._url(f'/api/v1/ausleihen/{loan_id}/verlaengern'),
            json={'langzeit': langzeit},
        )
        return self._handle_response(response)

    def return_loan(self, loan_id: int) -> dict:
        response = self.session.post(self._url(f'/api/v1/ausleihen/{loan_id}/rueckgabe'))
        return self._handle_response(response)

    def return_loan_with_condition(self, loan_id: int, zustand=None) -> dict:
        body = {}
        if zustand:
            body['zustand_bei_rueckgabe'] = zustand
        response = self.session.post(
            self._url(f'/api/v1/ausleihen/{loan_id}/rueckgabe'),
            json=body if body else None,
        )
        return self._handle_response(response)

    def get_overdue_loans(self) -> list:
        response = self.session.get(self._url('/api/v1/ausleihen/ueberfaellig'))
        return self._handle_response(response)

    # -------------------------------------------------------------------------
    # Reservierungen (Reservations)
    # -------------------------------------------------------------------------

    def get_reservations(self, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(self._url('/api/v1/reservierungen/'), params=params)
        return self._handle_response(response)

    def create_reservation(self, geraet_id: int, reserviert_fuer_datum: str) -> dict:
        data = {'geraet_id': geraet_id, 'reserviert_fuer_datum': reserviert_fuer_datum}
        response = self.session.post(self._url('/api/v1/reservierungen/'), json=data)
        return self._handle_response(response)

    def cancel_reservation(self, reservation_id: int) -> dict:
        response = self.session.delete(self._url(f'/api/v1/reservierungen/{reservation_id}'))
        return self._handle_response(response)

    # -------------------------------------------------------------------------
    # Benutzer (Users)
    # -------------------------------------------------------------------------

    def get_me(self) -> dict:
        response = self.session.get(self._url('/api/v1/benutzer/me'))
        return self._handle_response(response)

    def get_users(self, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(self._url('/api/v1/benutzer/'), params=params)
        return self._handle_response(response)

    def get_user(self, user_id: int) -> dict:
        response = self.session.get(self._url(f'/api/v1/benutzer/{user_id}'))
        return self._handle_response(response)

    def delete_user(self, user_id: int) -> dict:
        response = self.session.delete(self._url(f'/api/v1/benutzer/{user_id}'))
        return self._handle_response(response)

    def update_user_role(self, user_id: int, rolle: str) -> dict:
        response = self.session.patch(
            self._url(f'/api/v1/benutzer/{user_id}/rolle'),
            json={'rolle': rolle},
        )
        return self._handle_response(response)

    # -------------------------------------------------------------------------
    # Standort-Struktur
    # -------------------------------------------------------------------------

    def get_boxes(self, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(self._url('/api/v1/boxen/'), params=params)
        return self._handle_response(response)

    def get_box(self, box_id: int) -> dict:
        response = self.session.get(self._url(f'/api/v1/boxen/{box_id}'))
        return self._handle_response(response)

    def update_box(self, box_id: int, data: dict) -> dict:
        """Aktualisiert eine Box (Standort-Umzug, Beschreibung).
        Nutzt PUT gemäß Backend-Endpunkt PUT /api/v1/boxen/{box_id}.
        BoxUpdate erlaubt box_nummer, standort_id und beschreibung als optionale Felder.
        """
        response = self.session.put(self._url(f'/api/v1/boxen/{box_id}'), json=data)
        return self._handle_response(response)

    def get_standorte(self, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(self._url('/api/v1/standorte/'), params=params)
        return self._handle_response(response)

    def get_bildungseinrichtungen(self, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(self._url('/api/v1/bildungseinrichtungen/'), params=params)
        return self._handle_response(response)

    def create_box(self, data: dict) -> dict:
        response = self.session.post(self._url('/api/v1/boxen/'), json=data)
        return self._handle_response(response)

    def create_standort(self, data: dict) -> dict:
        response = self.session.post(self._url('/api/v1/standorte/'), json=data)
        return self._handle_response(response)

    def create_bildungseinrichtung(self, data: dict) -> dict:
        response = self.session.post(self._url('/api/v1/bildungseinrichtungen/'), json=data)
        return self._handle_response(response)

    # -------------------------------------------------------------------------
    # Export / Statistik / Audit
    # -------------------------------------------------------------------------

    def export_loans_csv(self, status=None, von=None, bis=None) -> requests.Response:
        params = {}
        if status: params['status'] = status
        if von: params['von'] = von
        if bis: params['bis'] = bis
        return self.session.get(self._url('/api/v1/export/ausleihen'), params=params)

    def get_statistik(self) -> dict:
        response = self.session.get(self._url('/api/v1/statistik/'))
        return self._handle_response(response)

    def get_audit_logs(self, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(self._url('/api/v1/audit-logs/'), params=params)
        return self._handle_response(response)

    def get_device_audit_logs(self, device_id: int, skip=0, limit=100) -> list:
        params = {'skip': skip, 'limit': limit}
        response = self.session.get(
            self._url(f'/api/v1/audit-logs/geraet/{device_id}'),
            params=params,
        )
        return self._handle_response(response)


def get_client(request) -> APIClient:
    return APIClient(
        base_url=settings.API_BASE_URL,
        token=getattr(request, 'api_token', None),
    )