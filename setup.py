from setuptools import setup

import tracked_model

setup(
    name='django-tracked-model',
    version=tracked_model.__version__,
    url='https://github.com/ojake/django-tracked-model',
    description=tracked_model.__doc__,
    author=tracked_model.__author__,
    author_email=tracked_model.__author_email__,
    packages=['tracked_model'],
    license='MIT',
    long_description=open('README').read(),
    install_requires=['django>=1.8.1'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ]
)
