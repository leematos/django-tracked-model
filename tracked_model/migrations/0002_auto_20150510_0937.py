# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('tracked_model', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='history',
            old_name='table_id',
            new_name='object_id',
        ),
        migrations.AddField(
            model_name='history',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', default=0),
            preserve_default=False,
        ),
        migrations.AlterIndexTogether(
            name='history',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='history',
            name='app_label',
        ),
        migrations.RemoveField(
            model_name='history',
            name='model_name',
        ),
    ]
