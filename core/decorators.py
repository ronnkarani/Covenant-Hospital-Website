from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def session_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_role"):
            messages.error(request, "Please log in to access the dashboard.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper
