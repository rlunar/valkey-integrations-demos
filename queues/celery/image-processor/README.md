# Celery with Valkey

If you are already running Redis OSS

Download image

```bash
podman pull redis:7.2.4-alpine
```

Run the server

```bash
podman run --name redis-oss -p 6380:6379 -d redis:7.2.4-alpine redis-server --save 60 1 --loglevel warning
```

Of if you are running RabbitMQ


```bash
podman pull rabbitmq:4-alpine
```


```bash
docker run -d -p 5672:5672 rabbitmq:4-alpine
```
