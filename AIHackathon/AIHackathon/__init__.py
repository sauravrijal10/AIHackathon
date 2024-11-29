from __future__ import absolute_import, unicode_literals
from AIHackathon.celery import app as celery_app

app = celery_app

__all__ = ('celery_app',)