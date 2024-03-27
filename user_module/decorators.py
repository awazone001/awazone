from functools import wraps
from django.shortcuts import render

def user_function(user):
    if user.is_staff:
        return False
    return True

def staff_function(user):
    if user.is_staff:
        return True
    return False

def admin_function(user):
    if user.is_superuser:
        return True
    return False

def user_access_only():
    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not user_function(request.user):
                return render(request,'user/op_error_403.html')
            return view(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def staff_access_only(view_to_retun = "loginpage"):
    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not staff_function(request.user):
                return render(request,'user/op_error_403.html')
            return view(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_access_only(message_to_deliver = "Not allowed to access the Admin page!"):
    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not admin_function(request.user):
                return render(request,'user/op_error_403.html')
            return view(request, *args, **kwargs)
        return _wrapped_view
    return decorator