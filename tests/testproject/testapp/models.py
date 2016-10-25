"""Models for testing"""
from django.db import models

from tracked_model.control import TrackedModelMixin


class BasicModel(TrackedModelMixin, models.Model):
    """Just few simple fields"""
    some_num = models.IntegerField()
    some_txt = models.TextField()
    some_date = models.DateField(null=True)
    some_img = models.ImageField(null=True)


class FKModel(TrackedModelMixin, models.Model):
    """Model with foreign key"""
    some_ip = models.GenericIPAddressField()
    basic = models.ForeignKey(BasicModel)


class M2MModel(TrackedModelMixin, models.Model):
    """Model with m2m key"""
    created = models.DateTimeField(auto_now_add=True)
    bunch = models.ManyToManyField(BasicModel)
