"""Models and tools for access control."""
from django.db import models
from django.apps import apps
from django.conf import settings

from tracked_model import serializer
from tracked_model.defs import REQUEST_CACHE_FIELD, ActionType, Field


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
    model_name = models.TextField()
    app_label = models.TextField()
    table_name = models.TextField()
    table_id = models.TextField()
    change_log = models.TextField()
    revision_author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True)
    revision_ts = models.DateTimeField(auto_now_add=True)
    revision_request = models.ForeignKey('RequestInfo', null=True)
    action_type = models.TextField(choices=ActionType.CHOICES)

    def __str__(self):
        template = '{0.model_name}/{0.revision_ts}/{0.revision_author}'
        return template.format(self)

    class Meta:
        """History meta options"""
        index_together = (('table_name', 'table_id'),)
        ordering = ('revision_ts',)
        get_latest_by = 'revision_ts'

    @property
    def _tracked_model(self):
        """Returns model tracked by this instance of ``History``"""
        return apps.get_model(self.app_label, self.model_name)

    def get_current_object(self):
        """Returns current instance of ``TrackedModel``
        that this ``History`` record belongs to
        """
        return self._tracked_model.objects.get(pk=self.table_id)

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
            model_name=self.model_name, app_label=self.app_label,
            table_id=self.table_id)
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
