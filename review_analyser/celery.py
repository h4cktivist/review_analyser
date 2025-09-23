import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'review_analyser.settings')

app = Celery('review_analyser')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
