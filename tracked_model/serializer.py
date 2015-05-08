"""Dump model and field data to dictionary"""
import json

from django.core.serializers.json import DjangoJSONEncoder

from tracked_model.defs import RELATED_FIELDS, FieldType, Field


def _basic_field_data(field, obj):
    """Returns ``obj.field`` data as a dict"""
    value = field.value_from_object(obj)
    return {Field.TYPE: FieldType.VAL, Field.VALUE: value}


def _related_field_data(field, obj):
    """Returns relation ``field`` as a dict.

    Dict contains related pk info and some meta information
    for reconstructing objects.
    """
    data = _basic_field_data(field, obj)
    relation_info = {
        Field.REL_DB_TABLE: field.rel.to._meta.db_table,
        Field.REL_APP: field.rel.to._meta.app_label,
        Field.REL_MODEL: field.rel.to.__name__
    }
    data[Field.TYPE] = FieldType.REL
    data[Field.REL] = relation_info
    return data


def _m2m_field_data(field, obj):
    """Returns m2m ``field`` as a dict.

    Value is an array of related primary keys and some meta information
    for reconstructing objects.
    """
    data = _basic_field_data(field, obj)
    data[Field.TYPE] = FieldType.M2M
    related = field.rel.to
    relation_info = {
        Field.REL_DB_TABLE: related._meta.db_table,
        Field.REL_APP: related._meta.app_label,
        Field.REL_MODEL: related.__name__
    }
    data[Field.REL] = relation_info
    value = data[Field.VALUE]
    value = [x[0] for x in value.values_list('pk')]
    data[Field.VALUE] = value
    return data


def dump_model(obj):
    """Returns ``obj`` as a dict.

    Returnded dic has a form of:
    {
        'field_name': {
            'type': `FieldType`,
            'value': field value,
            # if field is a relation, it also has:
            'rel': {
                'db_table': model db table,
                'app_label': model app label,
                'model_name': model name
            }
        }
    }
    """
    data = {}
    for field in obj._meta.fields:
        if isinstance(field, RELATED_FIELDS):
            field_data = _related_field_data(field, obj)
        else:
            field_data = _basic_field_data(field, obj)
        data[field.name] = field_data

    if obj.pk:
        for m2m in obj._meta.many_to_many:
            field_data = _m2m_field_data(m2m, obj)
            data[m2m.name] = field_data

    return data


def restore_model(cls, data):
    """Returns instance of ``cls`` with attributed loaded
    from ``data`` dict.
    """
    obj = cls()
    for field in data:
        setattr(obj, field, data[field][Field.VALUE])

    return obj


def to_json(data):
    """Returns data serialized to json using DjangoJSONEncoder"""
    return json.dumps(data, cls=DjangoJSONEncoder)


def from_json(json_data):
    """Returns data deserialized from json"""
    return json.loads(json_data, encoding='utf-8')
