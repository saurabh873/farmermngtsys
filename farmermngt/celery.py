from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmermngt.settings')

celery_app = Celery('farmermngt')

# Load task modules from all registered Django app configs
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()


from celery.schedules import crontab
from celery import Celery

app = Celery('farmer_management')

app.conf.beat_schedule = {
    'generate_monthly_report': {
        'task': 'users.tasks.generate_monthly_farmer_report',
        'schedule': crontab(minute=0, hour=0, day_of_month=1),  # Runs at midnight on the 1st of each month
    },
}
