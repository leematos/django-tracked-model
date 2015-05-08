"""Access control tools"""

from tracked_model import serializer
from tracked_model.defs import TrackToken, ActionType, Field


def create_track_token(request):
    """Returns ``TrackToken``.
    ``TrackToken' contains request and user making changes.

    It can be passed to ``TrackedModel.save`` instead of ``request``.
    It is intended to be used when passing ``request`` is not possible
    e.g. when ``TrackedModel.save`` will be called from celery task.
    """
    from tracked_model.models import RequestInfo
    request_pk = RequestInfo.create_or_get_from_request(request).pk
    user_pk = None
    if request.user.is_authenticated():
        user_pk = request.user.pk

    return TrackToken(request_pk=request_pk, user_pk=user_pk)


class TrackedModelMixin:
    """Adds change-tracking functionality to models.


    Makes ``save`` method accept ``request`` or ``track_token`` keywords.
    If one of them is used, changes will be stored to database.

    Changes can be then accessed through model's
    ``tracked_model_history`` method.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tracked_model_initial_state = serializer.dump_model(self)

    def save(self, *args, **kwargs):
        """Saves changes made on model instance if ``request`` or
        ``track_token`` keyword are provided.
        """
        from tracked_model.models import History, RequestInfo
        if self.pk:
            action = ActionType.UPDATE
            changes = None
        else:
            action = ActionType.CREATE
            changes = serializer.dump_model(self)

        request = kwargs.pop('request', None)
        track_token = kwargs.pop('track_token', None)

        super().save(*args, **kwargs)
        if not changes:
            changes = self._tracked_model_diff()

        if changes:
            hist = History()
            hist.model_name = self._meta.model.__name__
            hist.app_label = self._meta.app_label
            hist.table_name = self._meta.db_table
            hist.table_id = self.pk
            hist.change_log = serializer.to_json(changes)
            hist.action_type = action
            if request:
                if request.user.is_authenticated():
                    hist.revision_author = request.user
                req_info = RequestInfo.create_or_get_from_request(request)
                hist.revision_request = req_info
            elif track_token:
                hist.revision_author_id = track_token.user_pk
                hist.revision_request_id = track_token.request_pk

            hist.save()

        self._tracked_model_initial_state = serializer.dump_model(self)

    def delete(self, *args, **kwargs):
        """Saves history of model instance deletion"""
        from tracked_model.models import History, RequestInfo
        hist = History()
        hist.model_name = self._meta.model.__name__
        hist.app_label = self._meta.app_label
        hist.table_name = self._meta.db_table
        hist.table_id = self.pk
        hist.action_type = ActionType.DELETE
        state = serializer.dump_model(self)
        hist.change_log = serializer.to_json(state)
        request = kwargs.pop('request', None)
        track_token = kwargs.pop('track_token', None)
        if request:
            if request.user.is_authenticated():
                hist.revision_author = request.user
            req_info = RequestInfo.create_or_get_from_request(request)
            hist.revision_request = req_info
        elif track_token:
            hist.revision_author_id = track_token.user_pk
            hist.revision_request_id = track_token.request_pk

        hist.save()
        super().delete(*args, **kwargs)

    def _tracked_model_diff(self):
        """Returns changes made to model instance.
        Returns None if no changes were made.
        """
        initial_state = self._tracked_model_initial_state
        current_state = serializer.dump_model(self)
        if current_state == initial_state:
            return None

        change_log = {}
        for field in initial_state:
            old_value = initial_state[field][Field.VALUE]
            new_value = current_state[field][Field.VALUE]
            if old_value == new_value:
                continue
            field_data = initial_state.copy()[field]
            del field_data[Field.VALUE]
            field_data[Field.OLD] = old_value
            field_data[Field.NEW] = new_value
            change_log[field] = field_data

        return change_log or None

    def tracked_model_history(self):
        """Returns history of a tracked object"""
        from tracked_model.models import History
        return History.objects.filter(
            table_name=self._meta.db_table, table_id=self.pk)
