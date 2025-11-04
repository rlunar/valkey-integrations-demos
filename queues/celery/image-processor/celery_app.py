from celery import Celery
from config import Config

def make_celery():
    celery = Celery(
        'image_processor',
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=['tasks']
    )
    
    celery.conf.update(
        task_serializer=Config.CELERY_TASK_SERIALIZER,
        result_serializer=Config.CELERY_RESULT_SERIALIZER,
        accept_content=Config.CELERY_ACCEPT_CONTENT,
        timezone=Config.CELERY_TIMEZONE,
        enable_utc=Config.CELERY_ENABLE_UTC,
    )
    
    return celery

celery_app = make_celery()