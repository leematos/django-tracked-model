"""Models and tools for access control."""
import threading
from contextlib import contextmanager

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from . import serializer
from .defs import REQUEST_CACHE_FIELD, ActionType, Field


class RequestInfo(models.Model):
    """Stores information about request during which changes were made"""
    user_ip = models.GenericIPAddressField(null=True)
    user_host = models.TextField(null=True)
    user_agent = models.TextField(null=True)
    full_path = models.TextField(null=True)
    method = models.TextField(null=True)
    referer = models.TextField(null=True)
    tstamp = models.DateTimeField(null=False, auto_now_add=True)

    @staticmethod
    def create_or_get_from_request(request):
        """Returns `RequestInfo` instance.

        If object was already created during ``request`` it is
        returned. Otherwise new instance is created with details
        populated from ``request``. New instance is then cached for reuse
        on subsequential calls.
        """
        saved = getattr(request, REQUEST_CACHE_FIELD, None)
        if isinstance(saved, RequestInfo):
            return saved
        req = RequestInfo()
        req.user_ip = request.META.get('REMOTE_ADDR')
        req.user_host = request.META.get('REMOTE_HOST')
        req.user_agent = request.META.get('HTTP_USER_AGENT')
        req.full_path = request.build_absolute_uri(
            request.get_full_path())
        req.method = request.META.get('REQUEST_METHOD')
        req.referer = request.META.get('HTTP_REFERER')
        req.save()
        setattr(request, REQUEST_CACHE_FIELD, req)
        return req


class History(models.Model):
    """Stores history of changes to ``TrackedModel``"""
    _context = threading.local()

    content_type = models.ForeignKey(ContentType)
    object_id = models.TextField()
    obj = GenericForeignKey('content_type', 'object_id')

    table_name = models.TextField()
    change_log = models.TextField()
    revision_author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True)
    revision_ts = models.DateTimeField(auto_now_add=True)
    revision_request = models.ForeignKey('RequestInfo', null=True)
    action_type = models.TextField(choices=ActionType.CHOICES)

    def __str__(self):
        cls = self.content_type.model_class().__name__
        rev_ts = self.revision_ts
        action = self.get_action_type_display()
        return '{}/{}/{}'.format(cls, rev_ts, action)

    class Meta:
        """History meta options"""
        ordering = ('revision_ts',)
        get_latest_by = 'revision_ts'

    @property
    def _tracked_model(self):
        """Returns model tracked by this instance of ``History``"""
        return self.content_type.model_class()

    def set_request_info(self, token=None):
        """Sets request info to current instance.

        If executed within ``context`` then _context.request is used
        otherwise token is used (if available).
        """
        # Somehow pylint doesn't see the *_id for django fields
        # pylint: disable=attribute-defined-outside-init
        try:
            request = self._context.request
            if request.user.is_authenticated():
                self.revision_author = request.user
            req_info = RequestInfo.create_or_get_from_request(request)
            self.revision_request = req_info
        except AttributeError:
            if token:
                self.revision_author_id = token.user_pk
                self.revision_request_id = token.request_pk

    def get_current_object(self):
        """Returns current instance of ``TrackedModel``
        that this ``History`` record belongs to
        """
        return self._tracked_model.objects.get(pk=self.object_id)

    def materialize(self):
        """Returns instance of ``TrackedModel`` created from
        current ``History`` snapshot.
        To rollback to current snapshot, simply call ``save``
        on materialized object.
        """
        if self.action_type == ActionType.DELETE:
            # On deletion current state is dumped to change_log
            # so it's enough to just restore it to object
            data = serializer.from_json(self.change_log)
            obj = serializer.restore_model(self._tracked_model, data)
            return obj

        changes = History.objects.filter(
            content_type=self.content_type, object_id=self.object_id)
        changes = changes.filter(revision_ts__lte=self.revision_ts)
        changes = list(changes.order_by('revision_ts'))

        creation = changes.pop(0)
        data = serializer.from_json(creation.change_log)
        obj = serializer.restore_model(self._tracked_model, data)

        for change in changes:
            change_log = serializer.from_json(change.change_log)
            for field in change_log:
                next_val = change_log[field][Field.NEW]
                setattr(obj, field, next_val)

        return obj

    @classmethod
    @contextmanager
    def context(cls, request):
        """Add ``request`` to context and removes it on exit"""
        setattr(cls._context, 'request', request)
        yield
        delattr(cls._context, 'request')

    @classmethod
    def for_model(cls, model):
        """Returns history for ``model``"""
        content_type = ContentType.objects.get_for_model(model)
        return cls.objects.filter(content_type=content_type)
