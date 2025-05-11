import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# app.conf.update(
#     worker_state_db=None,
#     worker_persistent_revokes=False,
#     broker_connection_retry_on_startup=True
# )