import os

class Config:
    # Valkey Configuration
    VALKEY_URL = os.getenv('VALKEY_URL', 'redis://localhost:6379/0')
    
    # Celery Configuration
    CELERY_BROKER_URL = VALKEY_URL
    CELERY_RESULT_BACKEND = VALKEY_URL
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    
    # Application Configuration
    UPLOAD_FOLDER = 'uploads'
    THUMBNAIL_FOLDER = 'thumbnails'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Thumbnail Sizes
    THUMBNAIL_SIZES = {
        'small': (150, 150),
        'medium': (400, 400),
        'large': (800, 800)
    }