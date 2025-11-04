import os
from PIL import Image
from celery import group
from celery_app import celery_app
from config import Config

@celery_app.task(bind=True, name='tasks.process_image')
def process_image(self, image_path, filename):
    """
    Main task that orchestrates thumbnail generation.
    Creates a group of subtasks for parallel processing.
    """
    try:
        # Create thumbnail directories if they don't exist
        for size_name in Config.THUMBNAIL_SIZES.keys():
            os.makedirs(
                os.path.join(Config.THUMBNAIL_FOLDER, size_name), 
                exist_ok=True
            )
        
        # Create a group of thumbnail generation tasks
        job = group(
            generate_thumbnail.s(image_path, filename, size_name, dimensions)
            for size_name, dimensions in Config.THUMBNAIL_SIZES.items()
        )
        
        # Execute all thumbnail tasks in parallel
        result = job.apply_async()
        
        # Wait for all tasks to complete
        thumbnails = result.get()
        
        return {
            'status': 'success',
            'filename': filename,
            'thumbnails': thumbnails,
            'message': f'Generated {len(thumbnails)} thumbnails'
        }
    
    except Exception as e:
        # Update task state for error tracking
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise

@celery_app.task(name='tasks.generate_thumbnail')
def generate_thumbnail(image_path, filename, size_name, dimensions):
    """
    Generate a single thumbnail of specified size.
    """
    try:
        # Open the original image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Create thumbnail (maintains aspect ratio)
            img.thumbnail(dimensions, Image.Resampling.LANCZOS)
            
            # Generate output path
            name, ext = os.path.splitext(filename)
            thumbnail_filename = f"{name}_{size_name}{ext}"
            thumbnail_path = os.path.join(
                Config.THUMBNAIL_FOLDER, 
                size_name, 
                thumbnail_filename
            )
            
            # Save thumbnail
            img.save(thumbnail_path, quality=85, optimize=True)
            
            return {
                'size': size_name,
                'dimensions': dimensions,
                'path': thumbnail_path,
                'filename': thumbnail_filename
            }
    
    except Exception as e:
        return {
            'size': size_name,
            'error': str(e),
            'status': 'failed'
        }

@celery_app.task(name='tasks.cleanup_old_images')
def cleanup_old_images(days=7):
    """
    Periodic task to clean up old images and thumbnails.
    This can be scheduled using Celery Beat.
    """
    import time
    from pathlib import Path
    
    cutoff_time = time.time() - (days * 86400)
    cleaned_count = 0
    
    # Clean uploads
    for filepath in Path(Config.UPLOAD_FOLDER).glob('*'):
        if filepath.stat().st_mtime < cutoff_time:
            filepath.unlink()
            cleaned_count += 1
    
    # Clean thumbnails
    for size_folder in Path(Config.THUMBNAIL_FOLDER).iterdir():
        if size_folder.is_dir():
            for filepath in size_folder.glob('*'):
                if filepath.stat().st_mtime < cutoff_time:
                    filepath.unlink()
                    cleaned_count += 1
    
    return f"Cleaned up {cleaned_count} old files"
