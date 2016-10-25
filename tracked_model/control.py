"""Access control tools"""
from . import serializer
from .defs import TrackToken, ActionType, Field


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

    Changes executed through ``save`` or ``delete`` will be saved to
    the database (``History`` model).

    If request info is available it will also be saved (``RequestInfo`` model)

    Request info is available if ``save`` or ``delete`` are executed
    within ``History.context`` or if ``track_token`` keyword is
    provided to ``save`` or ``delete``.

    All views are executed within ``History.context`` if
    ``TrackedTokenMiddleware`` is active, otherwise one can
    manually call it:

        with History.context(request):
            some_model.save()

    If ``save`` or ``delete`` cannot be executed within request context
    e.g they are called by async task (e.g celery), ``track_token`` obtained
    by call to ``create_track_token`` can be passed as a keyword, e.g.

        token = create_track_token(request)
        some_task.delay(track_token=token)

        # inside ``some_task``:

        some_model.save(track_token=track_token)


    Changes to the model instance can be then accessed through model's
    ``tracked_model_history`` method.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tracked_model_initial_state = serializer.dump_model(self)

    def save(self, *args, **kwargs):
        """Saves history of changes, see class docstring for more details"""
        from tracked_model.models import History
        if self.pk:
            action = ActionType.UPDATE
            changes = None
        else:
            action = ActionType.CREATE
            changes = serializer.dump_model(self)

        track_token = kwargs.pop('track_token', None)

        super().save(*args, **kwargs)
        if not changes:
            changes = self._tracked_model_diff()

        if changes:
            hist = History()
            hist.obj = self
            hist.table_name = self._meta.db_table
            hist.table_id = self.pk
            hist.change_log = serializer.to_json(changes)
            hist.action_type = action
            hist.set_request_info(track_token)
            hist.save()

        self._tracked_model_initial_state = serializer.dump_model(self)

    def delete(self, *args, **kwargs):
        """Saves info about deletion, see class docstring for more details"""
        from tracked_model.models import History
        hist = History()
        hist.obj = self
        hist.table_name = self._meta.db_table
        hist.table_id = self.pk
        hist.action_type = ActionType.DELETE
        state = serializer.dump_model(self)
        hist.change_log = serializer.to_json(state)
        track_token = kwargs.pop('track_token', None)
        hist.set_request_info(track_token)
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
            field_data = initial_state[field].copy()
            del field_data[Field.VALUE]
            field_data[Field.OLD] = old_value
            field_data[Field.NEW] = new_value
            change_log[field] = field_data

        return change_log or None

    def tracked_model_history(self):
        """Returns history of a tracked object"""
        from tracked_model.models import History
        return History.for_model(self).filter(object_id=self.pk)
