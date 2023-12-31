from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mmoney.settings')

app = Celery('mmoney')

app.conf.broker_url = 'redis://localhost:6379/0'

app.conf.result_backend = 'redis://localhost:6379/0'


# app.conf.enable_utc = False

# app.conf.update(timezone = 'Africa/Nairobi')
# app.conf.timezone = 'Africa/Nairobi'

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')