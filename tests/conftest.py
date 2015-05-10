"""pytest configuration"""
import django
from django.conf import settings


def pytest_configure():
    """There is no project, only app, so we initialize django manually"""
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test.db'
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth', 'django.contrib.contenttypes',
            'tracked_model', 'tests'
        ]
    )

    django.setup()
