"""Tests middleware"""
# pylint: disable=import-error
from django.core.urlresolvers import reverse

import pytest

from testapp import models


pytestmark = pytest.mark.django_db


def test_create_has_request_info(admin_client):
    """Create ``BasicModel`` through view
    and check that history has request
    info attached to it.
    """
    assert models.BasicModel.objects.count() == 0
    url = reverse('new')
    data = {
        'some_txt': 'what',
        'some_num': 42,
        'some_date': '2016-01-01'
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302

    basic = models.BasicModel.objects.get()
    hist = basic.tracked_model_history().get()

    assert hist.revision_request is not None
