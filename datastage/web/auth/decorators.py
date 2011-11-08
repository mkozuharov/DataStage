import functools

from .views import LoginRequiredView

def login_required(view):
    return functools.wraps(view)(LoginRequiredView.as_view(protected_view=view))