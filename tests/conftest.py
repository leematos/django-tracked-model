"""pytest configuration"""
import os
import sys

import django


def pytest_configure():
    """Setup django testproject"""
    sys.path.append(os.path.abspath('./tests/testproject'))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'

    django.setup()
