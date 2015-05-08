"""Models for testing"""
import django
from django.db import models
from django.conf import settings

from tracked_model.control import TrackedModelMixin


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/test.db'
        }
    },
    INSTALLED_APPS=(
        'tests', 'tracked_model',
        'django.contrib.auth', 'django.contrib.contenttypes'
    )
)

django.setup()


class BasicModel(TrackedModelMixin, models.Model):
    """Just few simple fields"""
    some_num = models.IntegerField()
    some_txt = models.TextField()
    some_date = models.DateField(null=True)


class FKModel(TrackedModelMixin, models.Model):
    """Model with foreign key"""
    some_ip = models.GenericIPAddressField()
    basic = models.ForeignKey(BasicModel)


class M2MModel(TrackedModelMixin, models.Model):
    """Model with m2m key"""
    created = models.DateTimeField(auto_now_add=True)
    bunch = models.ManyToManyField(BasicModel)
