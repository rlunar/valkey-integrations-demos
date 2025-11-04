# Building a Scalable Image Processing Service with Celery and Valkey

## Introduction

Modern web applications frequently face a common challenge: how do you handle resource intensive operations without making users wait? Whether it's processing uploaded images, generating reports, or sending bulk emails, these tasks can significantly impact user experience if handled synchronously.

Enter _distributed task queues_ a pattern that allows applications to offload heavy work to background processes. In this tutorial, we will build a practical image processing service using Python's [Celery](https://docs.celeryq.dev/) task queue with [Valkey](https://valkey.io/) as the message broker.

**Why Valkey?** Valkey is a high performance, open source key value datastore and the natural evolution of the Redis community. As a Linux Foundation project, Valkey provides the reliability and performance you need for production workloads, backed by a truly open governance model that ensures the project remains community driven.

## The Use Case: Automated Thumbnail Generation

Imagine you are building a photo sharing application. Users upload high resolution images, but your application needs to display thumbnails in multiple sizes across different views:
- **Small thumbnails** (150x150px) for grid views
- **Medium thumbnails** (400x400px) for preview cards
- **Large thumbnails** (800x800px) for detail pages

Processing these thumbnails synchronously would mean users wait several seconds after each upload, unacceptable in modern web applications. Instead, we will use Celery to process images asynchronously, allowing users to continue using the app while thumbnails are generated in the background.

## Why This Architecture Matters

**The Problem:** Image processing is CPU intensive. A single high resolution image might take 2-3 seconds to process into multiple thumbnails. With synchronous processing:
- Users experience slow response times
- Your web server threads are blocked
- Scalability is limited by your web server capacity

**The Solution:** Asynchronous task processing with Celery and Valkey:
- Users get immediate upload confirmation
- Processing happens in dedicated worker processes
- You can scale workers independently of your web application
- Valkey efficiently manages the task queue with minimal latency

## Prerequisites

Before we begin, ensure you have:
- Python 3.8 or higher installed
- Basic familiarity with Python and web development
- Understanding of virtual environments (recommended)

## Setting Up Your Environment

### Installing Valkey

Valkey installation is straightforward. Choose the method that works best for your system:

**Using Docker (Recommended for development):**
```bash
docker run -d --name valkey -p 6379:6379 valkey/valkey:9-alpine
```

**On macOS with Homebrew:**
```bash
brew install valkey
valkey-server
```

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install valkey
sudo systemctl start valkey
```

**Building from source:**
```bash
git clone https://github.com/valkey-io/valkey.git
cd valkey
make
src/valkey-server
```

Verify Valkey is running:
```bash
valkey-cli ping
# Should return: PONG
```

### Setting Up Python Environment

Create a new project directory and set up a virtual environment:

```bash
mkdir image-processor
cd image-processor
```

Create a virtual environment using PIP:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Or using UV:

```bash
uv init -q
```

Install required packages:

```bash
pip install celery[redis] pillow flask flask-cors redis
```

Or using UV:

```bash
uv add celery[redis] pillow flask flask-cors redis
```

**Package breakdown:**
- `celery[redis]`: Celery with Redis/Valkey support
- `pillow`: Python Imaging Library for image processing
- `flask`: Lightweight web framework for our API
- `flask-cors`: Handle Cross-Origin Resource Sharing
- `redis`: Python client that works with Valkey

## Project Structure

Let's organize our project:

```bash
image-processor/
├── app.py              # Flask web application
├── celery_app.py       # Celery configuration
├── tasks.py            # Celery task definitions
├── config.py           # Configuration settings
├── uploads/            # Original uploaded images
├── thumbnails/         # Generated thumbnails
│   ├── small/
│   ├── medium/
│   └── large/
└── requirements.txt    # Python dependencies
```

## Implementation

### Step 1: Configuration

First, let's create our configuration file:

**config.py:**
```python
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
```

### Step 2: Celery Application Setup

Create the Celery application instance:

**celery_app.py:**
```python
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
```

### Step 3: Image Processing Tasks

Now for the core functionality—our Celery tasks:

**tasks.py:**
```python
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
```

### Step 4: Flask Web Application

Create the API endpoint for image uploads:

**app.py:**
```python
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from celery.result import AsyncResult
from tasks import process_image
from celery_app import celery_app
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Create necessary directories
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.THUMBNAIL_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Handle image upload and trigger asynchronous processing.
    """
    # Validate request
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Queue image processing task
    task = process_image.delay(filepath, filename)

    return jsonify({
        'message': 'Image uploaded successfully',
        'task_id': task.id,
        'filename': filename,
        'status_url': f'/status/{task.id}'
    }), 202

@app.route('/status/<task_id>', methods=['GET'])
def check_status(task_id):
    """
    Check the status of an image processing task.
    """
    task = AsyncResult(task_id, app=celery_app)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed...'
        }
    elif task.state == 'PROCESSING':
        response = {
            'state': task.state,
            'status': 'Task is being processed...'
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'error': str(task.info)
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }

    return jsonify(response)

@app.route('/thumbnail/<size>/<filename>', methods=['GET'])
def get_thumbnail(size, filename):
    """
    Serve a generated thumbnail.
    """
    if size not in Config.THUMBNAIL_SIZES:
        return jsonify({'error': 'Invalid thumbnail size'}), 400

    thumbnail_dir = os.path.join(Config.THUMBNAIL_FOLDER, size)
    return send_from_directory(thumbnail_dir, filename)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify service status.
    """
    # Check Valkey connection
    try:
        celery_app.broker_connection().ensure_connection(max_retries=3)
        valkey_status = 'connected'
    except Exception as e:
        valkey_status = f'disconnected: {str(e)}'

    return jsonify({
        'status': 'healthy',
        'valkey': valkey_status,
        'celery': 'configured'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

## Running Your Application

Now that we have all the pieces, let's run the application:

### Terminal 1: Start Valkey (if not already running)
```bash
valkey-server
```

### Terminal 2: Start Celery Worker
```bash
celery -A celery_app.celery_app worker --loglevel=info
```

For better performance, run multiple workers:
```bash
celery -A celery_app.celery_app worker --loglevel=info --concurrency=4
```

### Terminal 3: Start Flask Application
```bash
python app.py
```

## Testing Your Service

Let's test the image processing service using curl:

### 1. Upload an image
```bash
curl -X POST -F "image=@path/to/your/image.jpg" http://localhost:5000/upload
```

Response:
```json
{
  "message": "Image uploaded successfully",
  "task_id": "a7f3e4b2-1234-5678-90ab-cdef12345678",
  "filename": "image.jpg",
  "status_url": "/status/a7f3e4b2-1234-5678-90ab-cdef12345678"
}
```

### 2. Check processing status
```bash
curl http://localhost:5000/status/a7f3e4b2-1234-5678-90ab-cdef12345678
```

Response (in progress):
```json
{
  "state": "PROCESSING",
  "status": "Task is being processed..."
}
```

Response (completed):
```json
{
  "state": "SUCCESS",
  "result": {
    "status": "success",
    "filename": "image.jpg",
    "thumbnails": [
      {
        "size": "small",
        "dimensions": [150, 150],
        "path": "thumbnails/small/image_small.jpg",
        "filename": "image_small.jpg"
      },
      {
        "size": "medium",
        "dimensions": [400, 400],
        "path": "thumbnails/medium/image_medium.jpg",
        "filename": "image_medium.jpg"
      },
      {
        "size": "large",
        "dimensions": [800, 800],
        "path": "thumbnails/large/image_large.jpg",
        "filename": "image_large.jpg"
      }
    ],
    "message": "Generated 3 thumbnails"
  }
}
```

### 3. Retrieve a thumbnail
```bash
curl http://localhost:5000/thumbnail/medium/image_medium.jpg --output downloaded_thumbnail.jpg
```

## Best Practices and Production Considerations

### 1. Connection Pooling

Valkey connections should be pooled for optimal performance. Celery handles this automatically, but you can tune the pool size:

```python
# In celery_app.py
celery.conf.update(
    broker_pool_limit=10,  # Maximum number of connections in the pool
    broker_connection_retry_on_startup=True,
)
```

### 2. Task Routing

For larger applications, route different types of tasks to specialized workers:

```python
# In celery_app.py
celery.conf.update(
    task_routes={
        'tasks.process_image': {'queue': 'images'},
        'tasks.cleanup_old_images': {'queue': 'maintenance'},
    }
)
```

Start workers for specific queues:
```bash
# Image processing worker
celery -A celery_app.celery_app worker -Q images --concurrency=4

# Maintenance worker
celery -A celery_app.celery_app worker -Q maintenance --concurrency=1
```

### 3. Error Handling and Retries

Configure automatic retries for transient failures:

```python
@celery_app.task(
    bind=True,
    autoretry_for=(IOError, OSError),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True
)
def process_image(self, image_path, filename):
    # Task implementation
    pass
```

### 4. Monitoring with Flower

Install Flower for real-time monitoring:

```bash
pip install flower
flower -A celery_app.celery_app --port=5555
```

Access the dashboard at `http://localhost:5555`

### 5. Rate Limiting

Protect your service from overload:

```python
@celery_app.task(rate_limit='10/m')  # 10 tasks per minute
def process_image(image_path, filename):
    pass
```

### 6. Task Timeouts

Set reasonable timeouts to prevent stuck tasks:

```python
@celery_app.task(time_limit=300, soft_time_limit=270)  # 5 minutes hard, 4.5 soft
def process_image(image_path, filename):
    pass
```

### 7. Result Expiration

Clean up task results automatically:

```python
celery.conf.update(
    result_expires=3600,  # Results expire after 1 hour
)
```

## Performance Tuning with Valkey

### Persistence Configuration

For development, you might disable persistence for speed:

```bash
# In valkey.conf
save ""
appendonly no
```

For production, use appropriate persistence settings:

```bash
# In valkey.conf
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

### Memory Management

Configure Valkey memory limits and eviction policies:

```bash
# In valkey.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Connection Limits

Adjust connection limits for high-traffic scenarios:

```bash
# In valkey.conf
maxclients 10000
```

## Scaling Your Application

### Horizontal Scaling

Run multiple worker instances across different machines:

```bash
# On Machine 1
celery -A celery_app.celery_app worker --hostname=worker1@%h

# On Machine 2
celery -A celery_app.celery_app worker --hostname=worker2@%h
```

### Vertical Scaling

Increase worker concurrency based on CPU cores:

```bash
# Automatically use all CPU cores
celery -A celery_app.celery_app worker --autoscale=10,3
```

### Load Balancing

Use multiple Valkey instances with clustering for high availability.

## Why Valkey Makes a Difference

Throughout this tutorial, we've built a production-ready image processing service. Here's why Valkey is the ideal choice for this architecture:

**Performance**: Valkey's optimized data structures and efficient memory management ensure minimal latency for task queuing and result storage. In our tests, Valkey handles thousands of task enqueue/dequeue operations per second with sub-millisecond latency.

**Reliability**: As a Linux Foundation project, Valkey benefits from community-driven development and transparent governance. You're not dependent on a single vendor's roadmap or licensing decisions.

**Compatibility**: Valkey maintains protocol compatibility with Redis, making migration straightforward. Our Celery application works seamlessly with Valkey without any code changes—just point your connection string to Valkey instead of Redis.

**Open Source**: Valkey is truly open source under the BSD-3-Clause license. You have complete freedom to use, modify, and deploy it without concerns about licensing changes or enterprise upselling.

**Community**: The Valkey community is active and welcoming. Contributions are encouraged, and the project roadmap is shaped by actual user needs rather than commercial interests.

## Next Steps and Extensions

Ready to take this further? Here are some ideas:

1. **Add image filters**: Implement sepia, grayscale, or blur effects using Pillow
2. **Support more formats**: Add WebP conversion for smaller file sizes
3. **Implement progress tracking**: Use Celery's update_state for real-time progress
4. **Add batch processing**: Allow users to upload multiple images at once
5. **Create a web UI**: Build a React or Vue.js frontend
6. **Implement storage backends**: Integrate S3 or other cloud storage
7. **Add watermarking**: Automatically add watermarks to images
8. **Smart cropping**: Use AI for intelligent thumbnail cropping
9. **Schedule periodic tasks**: Use Celery Beat for automated maintenance
10. **Add authentication**: Implement user accounts and access control

## Join the Valkey Community

We'd love to hear about what you're building with Valkey! Here's how to get involved:

- **GitHub**: [github.com/valkey-io/valkey](https://github.com/valkey-io/valkey)
- **Documentation**: [valkey.io/docs](https://valkey.io/docs)
- **Community Forum**: Join discussions on GitHub Discussions
- **Stack Overflow**: Tag questions with `valkey`
- **Contributing**: We welcome contributions of all kinds

## Conclusion

In this tutorial, we've built a complete, production-ready image processing service using Celery and Valkey. We've covered:

- Setting up Valkey as a high-performance message broker
- Implementing asynchronous image processing with Celery
- Creating a RESTful API with Flask
- Following best practices for error handling, monitoring, and scaling
- Understanding why Valkey is the right choice for modern applications

The patterns and practices we've discussed apply to many other use cases beyond image processing—video transcoding, PDF generation, data analytics, email campaigns, and more. With Celery and Valkey, you have a powerful, scalable foundation for building distributed applications.

Remember, asynchronous processing isn't just about performance—it's about building better user experiences. By offloading heavy work to background tasks, you keep your applications responsive and your users happy.

Happy coding, and welcome to the Valkey community!

---

*Have questions or want to share what you've built? Connect with the Valkey community on GitHub or join our community discussions.*
