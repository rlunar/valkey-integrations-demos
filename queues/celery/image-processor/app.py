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
    app.run(debug=True, host='0.0.0.0', port=5050)