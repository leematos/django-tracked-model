"""Silently add request to ``History``"""
from .models import History


class TrackedModelMiddleware:
    """Expose request to ``History`` so it
    doesn't have to be added explicitly.

    If this middleware is active, every "save" and "delete" will
    have knowledge about request context that it was executed in.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Inject request into ``History.context`` for the duration
        of request.
        """
        with History.context(request):
            return self.get_response(request)
