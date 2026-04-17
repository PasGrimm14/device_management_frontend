"""URL configuration for the frontend app."""

from django.urls import path
from frontend.views import auth, dashboard, devices, loans, reservations, profile, admin_views, standort_views

urlpatterns = [
    # Auth
    path('login/', auth.login_view, name='login'),
    path('logout/', auth.logout_view, name='logout'),

    # Dashboard
    path('', dashboard.dashboard_view, name='dashboard'),

    # Devices
    path('geraete/', devices.device_list_view, name='device_list'),
    path('geraete/<int:device_id>/', devices.device_detail_view, name='device_detail'),
    path('geraete/<int:device_id>/bild/', devices.device_image_view, name='device_image'),
    path('geraete/<int:device_id>/qr-code/', devices.device_qr_download_view, name='device_qr_download'),

    # Loans
    path('ausleihen/', loans.loan_list_view, name='loan_list'),
    path('ausleihen/<int:loan_id>/', loans.loan_detail_view, name='loan_detail'),
    path('ausleihen/neu/<int:device_id>/', loans.loan_create_view, name='loan_create'),
    path('ausleihen/<int:loan_id>/verlaengern/', loans.loan_extend_view, name='loan_extend'),
    path('ausleihen/<int:loan_id>/rueckgabe/', loans.loan_return_view, name='loan_return'),

    # Reservations
    path('reservierungen/', reservations.reservation_list_view, name='reservation_list'),
    path('reservierungen/neu/<int:device_id>/', reservations.reservation_create_view, name='reservation_create'),
    path('reservierungen/<int:reservation_id>/stornieren/', reservations.reservation_cancel_view, name='reservation_cancel'),

    # Profile
    path('profil/', profile.profile_view, name='profile'),
    path('rolle-wechseln/', profile.role_switch_view, name='role_switch'),

    # Help & Scanner
    path('hilfe/', profile.help_view, name='help'),
    path('scanner/', profile.scanner_view, name='scanner'),

    # Admin views
    path('admin/geraete/', admin_views.admin_device_list_view, name='admin_device_list'),
    path('admin/geraete/neu/', admin_views.admin_device_create_view, name='admin_device_create'),
    path('admin/geraete/<int:device_id>/bearbeiten/', admin_views.admin_device_edit_view, name='admin_device_edit'),
    path('admin/geraete/<int:device_id>/loeschen/', admin_views.admin_device_delete_view, name='admin_device_delete'),
    path('admin/benutzer/', admin_views.admin_user_list_view, name='admin_user_list'),
    path('admin/benutzer/<int:user_id>/rolle/', admin_views.admin_user_role_view, name='admin_user_role'),
    path('admin/benutzer/<int:user_id>/loeschen/', admin_views.admin_user_delete_view, name='admin_user_delete'),
    path('admin/audit-logs/', admin_views.admin_audit_logs_view, name='admin_audit_logs'),
    path('admin/audit-logs/geraet/<int:device_id>/', admin_views.admin_device_audit_logs_view, name='admin_device_audit_logs'),

    # Admin - Standortverwaltung
    path('admin/standorte/', standort_views.admin_standort_list_view, name='admin_standort_list'),
    path('admin/standorte/einrichtung/neu/', standort_views.admin_bildungseinrichtung_create_view, name='admin_bildungseinrichtung_create'),
    path('admin/standorte/standort/neu/', standort_views.admin_standort_create_view, name='admin_standort_create'),
    path('admin/standorte/box/neu/', standort_views.admin_box_create_view, name='admin_box_create'),

    # Admin - Ausleihen-Verwaltung
    path('admin/ausleihen/', admin_views.admin_loan_list_view, name='admin_loan_list'),

    # Admin - Export
    path('admin/export/', admin_views.admin_export_view, name='admin_export'),

    # Admin - Statistik
    path('admin/statistik/', admin_views.admin_statistik_view, name='admin_statistik'),
]