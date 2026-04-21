# DHBW Heilbronn – Gerätemanagement Frontend

Django-basiertes Web-Frontend für das Gerätemanagementsystem der DHBW Heilbronn. Die Anwendung kommuniziert mit einem separaten FastAPI-Backend und stellt eine vollständige Benutzeroberfläche für die Ausleihe, Reservierung und Verwaltung von Geräten bereit.

---

## Inhaltsverzeichnis

- [Übersicht](#übersicht)
- [Features](#features)
- [Technologie-Stack](#technologie-stack)
- [Voraussetzungen](#voraussetzungen)
- [Installation & lokaler Start](#installation--lokaler-start)
- [Konfiguration](#konfiguration)
- [Docker](#docker)
- [Projektstruktur](#projektstruktur)
- [Rollen & Berechtigungen](#rollen--berechtigungen)
- [SSO-Authentifizierungsflow](#sso-authentifizierungsflow)
- [API-Integration](#api-integration)

---

## Übersicht

Das Frontend ist eine klassische Django-Webanwendung (Server-Side Rendering) ohne eigene Datenbank. Alle Daten werden über REST-API-Aufrufe an das Backend bezogen. Authentifizierung erfolgt per JWT-Token, das nach dem Login in der Django-Session gespeichert wird.

Im produktiven Betrieb ist eine Shibboleth-SSO-Anbindung vorgesehen. Im lokalen Testmodus erfolgt der Login manuell über Shibboleth-ID, Name und E-Mail-Adresse.

---

## Features

**Für alle Benutzer (Studierende & Mitarbeitende)**

- Geräteliste mit Suche und Filterung nach Status und Kategorie
- Gerätedetailseite mit Statusanzeige, Box-/Standortinformation und Gerätebild
- Ausleihe über QR-Code-Scan (Kamera) oder NFC-Tag
- Reservierung von Geräten für ein bestimmtes Datum
- Ausleihen verlängern (bis zu 2× je 14 Tage)
- Reservierungen stornieren
- Persönliches Profil mit Ausleihe- und Reservierungshistorie
- Integrierter QR- und NFC-Scanner

**Für Administratoren**

- Geräteverwaltung: Anlegen, Bearbeiten, Löschen von Geräten inkl. Bild-Upload
- Benutzerverwaltung: Rollen ändern, Benutzer löschen
- Standortverwaltung: Bildungseinrichtungen, Standorte und Boxen verwalten
- Ausleihen-Übersicht mit Rückgabe-Funktion und Zustandserfassung
- Überfällige Ausleihen anzeigen
- Audit-Logs systemweit oder gerätebezogen
- Statistik-Dashboard (Geräte, Ausleihen, Überfällige, Top-Geräte)
- CSV-Export von Ausleihdaten (gefiltert nach Status und Zeitraum)
- QR-Code-Download für einzelne Geräte
- **Rollenvorschau**: Admins können die App aus der User-Perspektive erleben (Role-Switch)

---

## Technologie-Stack

| Komponente | Version |
|---|---|
| Python | 3.11 |
| Django | 4.2 |
| Whitenoise | 6.6 (statische Dateien) |
| Requests | 2.31 (HTTP-Client für API-Calls) |
| python-dotenv | 1.0 |
| jsQR | 1.4.0 (QR-Erkennung im Browser, CDN) |

Kein JavaScript-Framework – alle Seiten werden server-seitig gerendert. Interaktivität (Scanner, Vorschau, Drag & Drop) ist in purem Vanilla-JS implementiert.

---

## Voraussetzungen

- Python 3.11+
- Ein laufendes FastAPI-Backend (URL konfigurierbar per `.env`)
- Optional: Docker & Docker Compose

---

## Installation & lokaler Start

```bash
# Repository klonen
git clone <repo-url>
cd device_management_frontend

# Virtuelle Umgebung erstellen und aktivieren
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env anpassen (siehe Abschnitt Konfiguration)

# Statische Dateien sammeln
python manage.py collectstatic --noinput

# Entwicklungsserver starten
python manage.py runserver 0.0.0.0:8050
```

Die Anwendung ist dann unter [http://localhost:8050](http://localhost:8050) erreichbar.

---

## Konfiguration

Alle Einstellungen werden über eine `.env`-Datei im Projektstamm gesetzt:

| Variable | Standard | Beschreibung |
|---|---|---|
| `SECRET_KEY` | *(Pflicht in Produktion)* | Django Secret Key |
| `DEBUG` | `True` | Debug-Modus aktivieren/deaktivieren |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Komma-getrennte Liste erlaubter Hosts |
| `API_BASE_URL` | `http://localhost:8000` | Interne URL des FastAPI-Backends (Server-zu-Server) |
| `API_PUBLIC_URL` | *(leer = API_BASE_URL)* | Öffentliche Backend-URL für Browser-seitige API-Calls (Scanner) |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8050` | Komma-getrennte Liste vertrauenswürdiger Origins |
| `LOGO_URL` | *(leer)* | URL des DHBW-Logos (z.B. externer CDN-Link) |
| `SYNC_URL` | `https://sync.heilbronn.dhbw.de` | Basis-URL von N'SYNC (SSO-Provider). Bei gesetztem Wert werden nicht-authentifizierte Nutzer automatisch dorthin weitergeleitet. |

**Hinweis zu `API_PUBLIC_URL`**: Der QR-/NFC-Scanner ruft die API direkt aus dem Browser auf. Wenn das Backend intern unter einer anderen URL erreichbar ist als für den Browser, muss `API_PUBLIC_URL` auf die öffentlich zugängliche Backend-URL gesetzt werden.

**Hinweis zu `SYNC_URL`**: Wenn gesetzt, leitet die `JWTAuthMiddleware` nicht-authentifizierte Nutzer direkt zu `{SYNC_URL}/accounts/sso/redirect/` weiter. N'SYNC übernimmt dann die Shibboleth-Authentifizierung und schickt den Nutzer mit einem One-Time-Token (OTT) zurück an `/sso/callback/?ott=<token>`. Ohne `SYNC_URL` fällt das System auf die lokale Login-Maske zurück.

---

## SSO-Authentifizierungsflow

```
Browser          Django-Frontend         N'SYNC (SSO)        FastAPI-Backend
  │                    │                     │                     │
  │─── GET /geraete/ ─►│                     │                     │
  │                    │ kein JWT in Session  │                     │
  │◄── redirect ───────│──────────────────►  │                     │
  │                    │   /accounts/sso/redirect/                 │
  │                    │                     │                     │
  │       Shibboleth-Authentifizierung       │                     │
  │◄──────────────────────────────────────── │                     │
  │─── GET /sso/callback/?ott=<token> ──────►│                     │
  │                    │ POST /api/v1/sso/callback {token}         │
  │                    │─────────────────────────────────────────►  │
  │                    │◄──────────────────── {access_token} ──────│
  │                    │ GET /api/v1/me (mit JWT)                  │
  │                    │─────────────────────────────────────────►  │
  │                    │◄──────────────────── {user_data} ─────────│
  │                    │ JWT + user in Session speichern           │
  │◄── redirect / ─────│                     │                     │
```

- **OTT (One-Time Token)**: Ein kurzlebiges, einmalig verwendbares Token von N'SYNC; wird gegen ein reguläres JWT beim Backend eingetauscht.
- **Fallback**: Ist `SYNC_URL` nicht gesetzt (lokale Entwicklung), wird zur internen Login-Maske unter `/login/` weitergeleitet.
- **Exempt Paths**: `/sso/callback/`, `/login/`, `/logout/` und `/static/` sind von der Middleware ausgenommen.

---

## Docker

### Einzelner Container

```bash
docker build -t dhbw-frontend .
docker run -p 8050:8050 \
  -e API_BASE_URL=http://backend:8000 \
  -e ALLOWED_HOSTS=yourdomain.com \
  -e SECRET_KEY=your-secret-key \
  dhbw-frontend
```

### Docker Compose

```bash
# .env anpassen, dann:
docker compose up -d
```

Die `docker-compose.yml` setzt das Frontend in ein externes `proxy-network` ein, das von einem vorgelagerten Nginx Proxy Manager genutzt wird. Der Netzwerkname kann in der Datei angepasst werden.

---

## Projektstruktur

```
device_management_frontend/
├── device_management_frontend/   # Django-Projektkonfiguration
│   ├── settings.py               # Zentrale Einstellungen
│   └── urls.py                   # Root-URL-Konfiguration
│
├── frontend/                     # Haupt-App
│   ├── views/                    # View-Module
│   │   ├── auth.py               # Login / Logout
│   │   ├── dashboard.py          # Dashboard
│   │   ├── devices.py            # Geräteliste & -detail
│   │   ├── loans.py              # Ausleihen
│   │   ├── reservations.py       # Reservierungen
│   │   ├── profile.py            # Profil, Hilfe, Scanner
│   │   ├── sso.py                # SSO-Callback (OTT → JWT)
│   │   ├── admin_views.py        # Admin: Geräte, Benutzer, Logs, Export, Statistik
│   │   └── standort_views.py     # Admin: Standortverwaltung
│   ├── services/
│   │   └── api_client.py         # Zentraler REST-API-Client
│   ├── templatetags/
│   │   └── frontend_tags.py      # Custom Template-Filter & Tags
│   ├── middleware.py             # JWT-Auth-Middleware
│   ├── decorators.py             # @login_required, @admin_required
│   ├── context_processors.py     # API_BASE_URL, LOGO_URL im Template-Kontext
│   └── urls.py                   # App-URL-Konfiguration
│
├── templates/
│   ├── base.html                 # Basis-Layout
│   ├── login.html                # Login-Seite (eigenständig)
│   ├── includes/                 # Wiederverwendbare Partials
│   │   ├── topbar.html
│   │   ├── sidebar.html
│   │   └── mobile_nav.html
│   └── frontend/                 # App-Templates
│       ├── dashboard.html
│       ├── devices.html
│       ├── device_detail.html
│       ├── loans.html
│       ├── loan_detail.html
│       ├── loan_extend.html
│       ├── loan_request.html
│       ├── reservations.html
│       ├── reservation_create.html
│       ├── profile.html
│       ├── scanner.html
│       ├── help.html
│       └── admin/
│           ├── devices.html
│           ├── device_form.html
│           ├── users.html
│           ├── loans.html
│           ├── audit_logs.html
│           ├── standorte.html
│           ├── standort_form.html
│           ├── statistik.html
│           └── export.html
│
├── static/
│   └── css/
│       └── main.css              # Gesamtes Stylesheet (CSS Custom Properties)
│
├── .env.example                  # Vorlage für Umgebungsvariablen
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Rollen & Berechtigungen

Das System kennt zwei Rollen, die vom Backend vergeben werden:

| Rolle | Bezeichner | Beschreibung |
|---|---|---|
| Studierende / Mitarbeitende | `Studierende_Mitarbeitende` | Standardrolle; kann Geräte einsehen, reservieren und Ausleihen verlängern |
| Administrator | `Administrator` | Vollzugriff; kann Geräte, Benutzer und Standorte verwalten, Rückgaben durchführen und auf alle Admin-Seiten zugreifen |

Admins können über den **Role-Switch** (Topbar) die App aus der Nutzerperspektive testen, ohne sich abmelden zu müssen. Der tatsächliche Datenbankzugriff bleibt dabei Admin-seitig – nur die UI-Ansicht ändert sich.

Die Zugriffssteuerung erfolgt über die Decorators `@login_required` und `@admin_required` in `frontend/decorators.py`.

---

## API-Integration

Der gesamte Backend-Zugriff läuft über `frontend/services/api_client.py`. Die Klasse `APIClient` kapselt alle Endpunkte:

- **Auth**: `POST /api/v1/auth/token`
- **Geräte**: CRUD unter `/api/v1/geraete/`, inkl. QR-Code und Bild
- **Ausleihen**: `/api/v1/ausleihen/` inkl. Verlängerung und Rückgabe
- **Reservierungen**: `/api/v1/reservierungen/`
- **Benutzer**: `/api/v1/benutzer/`
- **Standorte**: Boxen, Standorte, Bildungseinrichtungen
- **Audit-Logs**: `/api/v1/audit-logs/`
- **Statistik**: `/api/v1/statistik/`
- **Export**: `/api/v1/export/ausleihen` (CSV)

Der QR-/NFC-Scanner ruft die Scan-Endpunkte direkt aus dem Browser auf (`/api/v1/geraete/{id}/scan-ausleihe` und `/api/v1/geraete/{id}/scan-rueckgabe`). Hierfür wird `API_PUBLIC_URL` verwendet, da diese Calls den Umweg über Django umgehen.

Gerätebilder und QR-Codes werden hingegen durch Django proxied, sodass weder JWT-Token noch Presigned-URLs an den Browser weitergegeben werden.
