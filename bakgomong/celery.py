# celery.py
import os
from django.conf import settings
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bakgomong.settings')

app = Celery('bakgomong', broker=settings.BROKER_URL)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True

# Serialization format (JSON is a common choice)
app.conf.accept_content = ["json"]
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"

app.conf.worker_concurrency = 2  # The number of worker processes
app.conf.worker_prefetch_multiplier = 1  # Adjust based on your tasks
app.conf.worker_max_tasks_per_child = 100

# Logging (configure as needed)
app.conf.worker_send_task_events = True
app.conf.worker_disable_rate_limits = True
app.conf.task_acks_late = True

# Task result expiration time (adjust as needed)
app.conf.result_expires = 3600 * 24  # 24 hour

# Task time limits
app.conf.task_time_limit = 3600  # 1 hour
app.conf.task_soft_time_limit = 300  # 5 minutes

app.autodiscover_tasks()
