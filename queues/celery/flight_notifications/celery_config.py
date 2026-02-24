# celery_config.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Valkey/Redis connection URL
VALKEY_URL = os.getenv('VALKEY_URL', 'redis://localhost:6379/0')

# Initialize Celery
celery_app = Celery(
    'flight_notifications',
    broker=VALKEY_URL,
    backend=VALKEY_URL
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
    },
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge task after execution
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    
    # Task routing
    task_routes={
        'tasks.send_email_notification': {'queue': 'email'},
        'tasks.send_sms_notification': {'queue': 'sms'},
        'tasks.send_push_notification': {'queue': 'push'},
    },
)

# Task autodiscovery
celery_app.autodiscover_tasks(['tasks'])
