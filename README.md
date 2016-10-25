django-tracked-model
================


**Simple django app for tracking db changes executed through orm. (Only tested on python3.4 and django-1.10.1)**


# Usage

## Basic usage

**Once installed (see `Installation` below), every change to tracked model will be recorded whenever ``save`` or ``delete`` is called.**


## Advanced options

If model uses ``TrackedModelMixin`` changes will always be saved if made with ``save`` or ``delete``.

Additionally to changes, some meta information can also be saved (user making changes, IP etc). To enable this behaviour ``save`` or ``delete`` have to be called within ``History.context``. This can be done adding ``tracked_model.middleware.TrackedModelMiddleware`` to ``settings.MIDDLEWARE`` or manually:

    >>> with History.context(request):
    >>>     some_obj.save()

Also ``track_token`` kwarg can be added to ``save`` or ``delete`` if request is not available (for example inside celery task).
It should contain result of ``create_track_token(request)``.


To access model's history, call it's ``tracked_model_history`` method


    >>> history = model.tracked_model_history()
    >>> history
    >>> [<History: MyModel/2015-05-10 10:23:11.123512+00:00/Created>,
         <History: MyModel/2015-05-10 11:01:39.312233+00:00/Updated>,
         <History: MyModel/2015-05-10 11:05:05.123534+00:00/Updated>]


``History`` object contains timestamp and snapshot of changes made to an object, if ``save`` or ``delete`` was called within request context, it will also contain author of changes and some connection meta data.


Each snapshot can be used to recreate object from historical state with ``materialize`` method

    >>> hist_create = history.first()
    >>> model_at_creation = hist_create.materialize()

To rollback object to this state simply save it

    >>> model_at_creation.save()

All the changes are now discarded and model state is the same as of creation.



# Installation

0. 



    ```sh
    $ pip install django-tracked-model
    ```

1. Add ``tracked_model`` to ``INSTALLED_APPS`` in ``settings``.


2. Add ``tracked_model.middleware.TrackedModelMiddleware`` to ``MIDDLEWARE`` in ``settings``.


3. Synch db


    ```sh
    $ python manage.py migrate tracked_model
    ```


4. Mark model as trackable


```
from django.db import models
from tracked_model.control import TrackedModelMixin as Tracked

class MyModel(Tracked, models.Model):
    spam = models.IntegerField()
    egg = models.TextField()
```


# TODO

Restoring objects with ManyToMany is not yet tested and probably won't work.


# Tests & mods

If for some weird reason you want to hack around, clone repo and install stuff from dev-reqs.txt


```sh
$ pip install -r dev-reqs.txt

```

There is a Makefile with some handy shortcuts e.g.

```sh
$ make test
$ make qa
```

Poke around Makefile for details
