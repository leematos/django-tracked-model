"""Some static values definitions"""
from collections import namedtuple

from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.related import OneToOneField, ForeignKey


RELATED_FIELDS = (OneToOneField, ForeignKey)

REQUEST_CACHE_FIELD = '_tracked_model_request_info'

TrackToken = namedtuple('TrackToken', ('request_pk', 'user_pk'))


class ActionType:
    """Available action types for ``History``"""
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    CHOICES = (
        (CREATE, _('Created')),
        (UPDATE, _('Updated')),
        (DELETE, _('Deleted'))
    )


class FieldType:
    """Supported field types"""
    VAL = 'val'
    REL = 'rel'
    M2M = 'm2m'


class Field:
    """Available attributes stored for a field"""
    TYPE = 'type'
    VALUE = 'value'
    REL = 'rel'
    REL_DB_TABLE = 'table'
    REL_APP = 'label'
    REL_MODEL = 'model'
    NEW = 'new'
    OLD = 'old'
