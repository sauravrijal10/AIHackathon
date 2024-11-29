from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab  # Import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'run-this-task-every-day': {
        'task': 'myapp.tasks.my_scheduled_task',
        'schedule': crontab(minute="00", hour="7"),  # Executes every day at 7 AM
    },
}

app.conf.timezone = 'UTC'