"""Shortcuts"""
from django.views.generic import edit as edit_views

from tracked_model.control import TrackingFormViewMixin as TrackedView


class TrackedCreateView(TrackedView, edit_views.CreateView):
    """CreateView that tracks changes"""


class TrackedUpdateView(TrackedView, edit_views.UpdateView):
    """UpdateView that track changes"""


class TrackedDeleteView(TrackedView, edit_views.DeleteView):
    """DeleteView that track changes"""
