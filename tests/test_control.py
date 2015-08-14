"""Test for ``control`` module"""
# pylint: disable=unexpected-keyword-arg
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType

import pytest

from tests import models

from tracked_model.defs import ActionType
from tracked_model.models import History
from tracked_model.control import create_track_token, TrackingFormViewMixin


pytestmark = pytest.mark.django_db


def test_tracked_model_diff():
    """Test ``TrackedModelMixin._tarcked_model_diff``"""
    model = models.BasicModel.objects.create(some_num=3, some_txt='lol')
    diff = model._tracked_model_diff()

    assert diff is None
    model.some_txt = 'omg'
    diff = model._tracked_model_diff()
    assert diff is not None
    model.save()
    diff = model._tracked_model_diff()
    assert diff is None


def test_tracked_model_save_and_delete_and_model_history_with_no_request():
    """Test ``TrackedModel`` saving and deleting without request"""
    model = models.BasicModel(some_num=3, some_txt='lol')
    history = model.tracked_model_history
    assert history().count() == 0
    model.save()
    assert history().count() == 1
    assert history().first().action_type == ActionType.CREATE
    model.some_num = 3
    model.save()
    assert history().count() == 1
    model.some_num = 5
    model.save()
    assert history().count() == 2
    content_type = ContentType.objects.get_for_model(model)
    raw_history = History.objects.filter(
        content_type=content_type, object_id=model.pk)
    assert raw_history.count() == 2
    model.delete()
    assert raw_history.count() == 3
    assert raw_history.filter(action_type=ActionType.CREATE).count() == 1
    assert raw_history.filter(action_type=ActionType.DELETE).count() == 1
    assert not History.objects.filter(
        revision_author__isnull=False).exists()


def test_tracked_model_save_and_delete_and_model_history_with_request(
        rf, admin_user):
    """Test ``TrackedModel`` saving and deleting with authenticated request
    """
    request = rf.get('/')
    request.user = admin_user
    request.is_authenticated = lambda: True
    model = models.BasicModel(some_num=3, some_txt='lol')
    history = model.tracked_model_history
    assert history().count() == 0
    model.save(request=request)
    assert history().count() == 1
    assert history().first().action_type == ActionType.CREATE
    model.some_num = 3
    model.save(request=request)
    assert history().count() == 1
    model.some_num = 5
    model.save(request=request)
    assert history().count() == 2
    content_type = ContentType.objects.get_for_model(model)
    raw_history = History.objects.filter(
        content_type=content_type, object_id=model.pk)
    assert raw_history.count() == 2
    model.delete(request=request)
    assert raw_history.count() == 3
    assert raw_history.filter(action_type=ActionType.CREATE).count() == 1
    assert raw_history.filter(action_type=ActionType.DELETE).count() == 1
    assert not History.objects.filter(revision_author__isnull=True).exists()

    assert raw_history.filter(revision_author=admin_user).count() == 3


def test_tracked_model_save_and_delete_and_model_history_with_token(
        rf, admin_user):
    """Test ``TrackedModel`` saving and deleting with authenticated request
    """
    request = rf.get('/')
    request.user = admin_user
    request.is_authenticated = lambda: True
    token = create_track_token(request)
    model = models.BasicModel(some_num=3, some_txt='lol')
    history = model.tracked_model_history
    assert history().count() == 0
    model.save(track_token=token)
    assert history().count() == 1
    assert history().first().action_type == ActionType.CREATE
    model.some_num = 3
    model.save(track_token=token)
    assert history().count() == 1
    model.some_num = 5
    model.save(track_token=token)
    assert model.tracked_model_history().count() == 2
    content_type = ContentType.objects.get_for_model(model)
    raw_history = History.objects.filter(
        content_type=content_type, object_id=model.pk)
    assert raw_history.count() == 2
    model.delete(track_token=token)
    assert raw_history.count() == 3
    assert raw_history.filter(action_type=ActionType.CREATE).count() == 1
    assert raw_history.filter(action_type=ActionType.DELETE).count() == 1
    assert not History.objects.filter(revision_author__isnull=True).exists()

    assert raw_history.filter(revision_author=admin_user).count() == 3


def test_tracking_form_mixin_save(rf):
    """Tests TrackingFormViewMixin.form_valid"""
    view = TrackingFormViewMixin()
    view.request = rf.get('/')
    view.get_success_url = MagicMock()
    form = MagicMock()
    view.form_valid(form)
    assert view.get_success_url.called
    assert form.save.called
    

def test_tracking_form_mixin_delete(rf):
    """Tests TrackingFormViewMixin.delete"""
    view = TrackingFormViewMixin()
    request = rf.get('/')
    request.user = MagicMock(is_authenticated=lambda: False)
    obj = models.BasicModel.objects.create(some_num=3, some_txt='lol')
    obj_pk = obj.pk
    content_type = ContentType.objects.get_for_model(obj)
    raw_history = History.objects.filter(
        content_type=content_type, object_id=obj_pk)
    assert  raw_history.count() == 1
    view.get_object = lambda: obj
    view.get_success_url = MagicMock()
    view.delete(request)
    assert raw_history.count() == 2
