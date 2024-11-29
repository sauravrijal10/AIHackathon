from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab  # Import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIHackathon.settings')

app = Celery('AIHackathon')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.broker_url = 'redis://localhost:6379/0'  # Use Redis as the broker

app.conf.beat_schedule = {
    'run-this-task-every-day': {
        'task': 'cronjob.task.process_overdue_cases',
        'schedule': crontab(minute='*'),  # Executes every day at 7 AM
    },
}

app.conf.timezone = 'UTC'