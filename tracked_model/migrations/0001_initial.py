# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.TextField()),
                ('app_label', models.TextField()),
                ('table_name', models.TextField()),
                ('table_id', models.TextField()),
                ('change_log', models.TextField()),
                ('revision_ts', models.DateTimeField(auto_now_add=True)),
                ('action_type', models.TextField(choices=[('create', 'Created'), ('update', 'Updated'), ('delete', 'Deleted')])),
                ('revision_author', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('revision_ts',),
                'get_latest_by': 'revision_ts',
            },
        ),
        migrations.CreateModel(
            name='RequestInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_ip', models.GenericIPAddressField(null=True)),
                ('user_host', models.TextField(null=True)),
                ('user_agent', models.TextField(null=True)),
                ('full_path', models.TextField(null=True)),
                ('method', models.TextField(null=True)),
                ('referer', models.TextField(null=True)),
                ('tstamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='history',
            name='revision_request',
            field=models.ForeignKey(null=True, to='tracked_model.RequestInfo'),
        ),
        migrations.AlterIndexTogether(
            name='history',
            index_together=set([('table_name', 'table_id')]),
        ),
    ]
