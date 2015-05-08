"""Test for ``serializer`` module"""
import json

import pytest

from tests import models

from tracked_model import serializer, defs


pytestmark = pytest.mark.django_db


def _basic_model():
    """Returns ``BasicModel`` instance"""
    return models.BasicModel.objects.create(some_num=3, some_txt='lol')


def _fk_model():
    """Returns ``FKModel`` instance"""
    return models.FKModel.objects.create(
        some_ip='127.0.0.1', basic=_basic_model())


def _m2m_model():
    """Returns ``M2MModel`` instance"""
    model = models.M2MModel()
    model.save()
    model.bunch.add(_basic_model())
    model.bunch.add(_basic_model())
    return model


def test_dump_basic_model():
    """Test ``serializers.dump_model`` for model with only basic fields"""
    model = _basic_model()
    dumped = serializer.dump_model(model)
    assert len(dumped) == len(model._meta.fields)
    names = [x.name for x in model._meta.fields]
    assert set(names) == set(dumped.keys())


def test_dump_foreign_key_model():
    """Test ``serializers.dump_model`` for model with FK relation"""
    model = _fk_model()
    dumped = serializer.dump_model(model)
    assert len(dumped) == len(model._meta.fields)


def test_dump_m2m_model():
    """Test ``serializers.dump_model`` for model with m2m relation"""
    model = _m2m_model()
    dumped = serializer.dump_model(model)
    assert len(dumped['bunch'][defs.Field.VALUE]) == model.bunch.count()


def test_to_json():
    """Tests ``serializers.to_json``"""
    data = {'lol': 'wut', 'omg': 5}
    serialized = serializer.to_json(data)
    deserialized = json.loads(serialized)

    assert deserialized == data
