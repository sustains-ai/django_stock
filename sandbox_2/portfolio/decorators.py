from django.core.exceptions import PermissionDenied
from .models import FundManager


def fund_manager_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        try:
            request.user.fundmanager
        except FundManager.DoesNotExist:
            raise PermissionDenied("You must be a fund manager.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
