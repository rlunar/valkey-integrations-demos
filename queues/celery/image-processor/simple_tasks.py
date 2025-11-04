from celery import Celery

broker_name = 'redis'
broker_host = 'localhost'
broker_port = 6380

backend_name = 'redis'
backend_host = 'localhost'
backend_port = 6379

app = Celery('tasks', backend=f"{broker_name}://{broker_host}:{broker_port}", broker=f"{broker_name}://{broker_host}:{broker_port}")

@app.task
def add(x, y):
    return x + y
