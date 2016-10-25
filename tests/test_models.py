"""Test some model methods"""
# pylint: disable=import-error
from django.contrib.contenttypes.models import ContentType

import pytest

from tracked_model.defs import REQUEST_CACHE_FIELD
from tracked_model.models import RequestInfo, History

from testapp.models import BasicModel, FKModel


pytestmark = pytest.mark.django_db


def test_history_str_and_get_object_current_instance():
    """Test ``History.get_object_current_instance"""
    model = BasicModel.objects.create(some_num=42, some_txt='Cheese')

    history = model.tracked_model_history
    history_create = history().latest()
    model.some_txt = 'Spam'
    model.save()
    history_change = history().latest()

    assert history_create != history_change
    obj1 = history_create.get_current_object()
    obj2 = history_change.get_current_object()
    assert obj1 == obj2

    assert 'BasicModel' in str(history_create)

    model.delete()
    with pytest.raises(BasicModel.DoesNotExist):
        history_create.get_current_object()


def test_request_info_cached(rf):
    """Tests ``RequestInfo`` being cached for single request"""
    request = rf.get('/')

    req_info1 = RequestInfo.create_or_get_from_request(request)
    req_info2 = RequestInfo.create_or_get_from_request(request)
    assert req_info1 == req_info2
    delattr(request, REQUEST_CACHE_FIELD)
    req_info3 = RequestInfo.create_or_get_from_request(request)
    assert req_info3 != req_info1
    req_info4 = RequestInfo.create_or_get_from_request(request)
    assert req_info3 == req_info4


def test_materialize():
    """Tests ``History.materialize`` can restore object"""
    txt1 = 'spam'
    txt2 = 'ham'
    txt3 = 'egg'

    obj = BasicModel.objects.create(some_num=42, some_txt=txt1)
    obj_pk = obj.pk
    content_type = ContentType.objects.get_for_model(obj)
    hist1 = obj.tracked_model_history().latest()

    obj.some_txt = txt2
    obj.save()
    hist2 = obj.tracked_model_history().latest()

    obj.some_txt = txt3
    obj.save()
    hist3 = obj.tracked_model_history().latest()

    assert hist3.materialize().some_txt == txt3
    assert hist2.materialize().some_txt == txt2
    assert hist1.materialize().some_txt == txt1
    obj.delete()
    hist4 = History.objects.filter(
        content_type=content_type, object_id=obj_pk).latest()

    assert hist4.materialize().some_txt == txt3
    with pytest.raises(BasicModel.DoesNotExist):
        hist4.get_current_object()

    assert BasicModel.objects.count() == 0
    hist1.materialize().save()
    assert BasicModel.objects.count() == 1
    assert BasicModel.objects.first().some_txt == txt1

    obj = BasicModel.objects.create(some_num=42, some_txt=txt1)
    robj = FKModel.objects.create(some_ip='127.0.0.1', basic=obj)
    rhist = robj.tracked_model_history().latest()
    hobj = rhist.materialize()
    assert hobj.some_ip == robj.some_ip
    assert hobj.basic == robj.basic


def test_history_context():
    """Test that request is added for duration of ``context`` and removed
    on exit.
    """
    request = 'this would normally be django HttpRequest object'
    assert not getattr(History()._context, 'request', None)
    with History.context(request):
        assert getattr(History()._context, 'request', None) == request
    assert not getattr(History()._context, 'request', None)
