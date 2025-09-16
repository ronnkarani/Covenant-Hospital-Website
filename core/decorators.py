from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def session_required(view_func):
    """
    Ensures the user is logged in via hospital session (doctor/patient).
    If not, redirects to login page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get("user_role"):
            messages.error(request, "You must log in to access this page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

