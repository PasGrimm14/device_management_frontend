"""
Decorators for DHBW Gerätemanagement Frontend.
Provides login_required and admin_required decorators.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def login_required(view_func):
    """
    Decorator that redirects to /login/ if the user is not authenticated.
    A user is considered authenticated if request.api_token is set.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.api_token:
            messages.warning(request, 'Bitte melden Sie sich an, um fortzufahren.')
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """
    Decorator that requires the user to be an Administrator.
    Redirects to dashboard with error message if not admin.
    Also implies login_required.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.api_token:
            messages.warning(request, 'Bitte melden Sie sich an, um fortzufahren.')
            return redirect('/login/')

        user = request.current_user
        if not user or user.get('rolle') != 'Administrator':
            messages.error(request, 'Zugriff verweigert. Administratorrechte erforderlich.')
            return redirect('/')

        return view_func(request, *args, **kwargs)
    return wrapper
