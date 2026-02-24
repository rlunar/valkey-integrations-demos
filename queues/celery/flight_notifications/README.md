# Flight Notification System

A production-ready flight notification system using Celery, Valkey/Redis, and Pydantic that sends multi-channel notifications (Email, SMS, Push) when flight statuses change.

## Features

- ✅ Asynchronous task processing with Celery
- ✅ High-performance message brokering with Valkey (Redis-compatible)
- ✅ Type-safe data validation with Pydantic
- ✅ Multiple notification channels (Email, SMS, Push)
- ✅ Passenger notification preferences
- ✅ Automatic retry on failure
- ✅ Scalable architecture
- ✅ Task monitoring with Flower

## Architecture

```
┌─────────────────┐
│  Main App       │
│  (main.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Celery Tasks   │
│  (tasks.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Valkey/Redis   │◄─────┤ Celery Workers   │
│  Message Broker │      │ (email/sms/push) │
└─────────────────┘      └──────────────────┘
```

## Prerequisites

- Python 3.9+
- Docker (for running Valkey/Redis)
- pip

## Installation

1. Clone the repository or download the files

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Start Valkey/Redis using Docker:
```bash
docker run -d --name valkey -p 6379:6379 valkey/valkey:latest
```

Or if using Redis:
```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

## Running the System

### Step 1: Start Celery Workers

Open **three separate terminal windows** and start workers for each queue:

**Terminal 1 - Email Worker:**
```bash
celery -A celery_config worker --loglevel=info -Q email -n email_worker@%h
```

**Terminal 2 - SMS Worker:**
```bash
celery -A celery_config worker --loglevel=info -Q sms -n sms_worker@%h
```

**Terminal 3 - Push Notification Worker:**
```bash
celery -A celery_config worker --loglevel=info -Q push -n push_worker@%h
```

### Step 2: (Optional) Start Flower for Monitoring

In a **fourth terminal window**:
```bash
celery -A celery_config flower --port=5555
```

Visit http://localhost:5555 to monitor tasks in real-time.

### Step 3: Run the Demo

In a **fifth terminal window**:
```bash
python main.py
```

## Project Structure

```
flight-notifications/
├── models.py              # Pydantic data models
├── tasks.py               # Celery task definitions
├── celery_config.py       # Celery configuration
├── main.py                # Demo application
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
└── README.md             # This file
```

## How It Works

1. **Flight Status Changes**: The main application creates a flight with passengers and simulates status changes (delayed, boarding, departed)

2. **Task Distribution**: When a status changes, the `notify_passengers` task:
   - Validates flight and passenger data using Pydantic
   - Creates notification tasks for each passenger based on their preferences
   - Distributes tasks to appropriate queues (email, sms, push)

3. **Worker Processing**: Celery workers process tasks from their respective queues:
   - Email workers send email notifications
   - SMS workers send SMS notifications
   - Push workers send push notifications

4. **Retry Logic**: Failed tasks are automatically retried up to 3 times with a 5-second delay

## Data Models

### Passenger
```python
{
    "passenger_id": "P001",
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice@example.com",
    "phone_number": "+1234567890",
    "push_token": "expo_token_123",
    "preferred_notifications": ["email", "sms", "push"]
}
```

### Flight
```python
{
    "flight_number": "AA101",
    "airline": "American Airlines",
    "origin": "JFK",
    "destination": "LAX",
    "scheduled_departure": "2025-11-05T10:00:00",
    "scheduled_arrival": "2025-11-05T13:30:00",
    "status": "scheduled",
    "gate": "B22",
    "passengers": [...]
}
```

## Configuration

### Celery Configuration (celery_config.py)

- **Task Serialization**: JSON for interoperability
- **Result Expiration**: 1 hour
- **Task Acknowledgment**: Late acknowledgment (after execution)
- **Worker Prefetch**: 1 task at a time for even distribution
- **Queue Routing**: Automatic routing to email/sms/push queues

### Task Retry Settings

- **Max Retries**: 3 attempts
- **Retry Delay**: 5 seconds between attempts
- **Auto Retry**: Enabled for all exceptions

## Extending the System

### Adding New Notification Channels

1. Add new notification type to `models.py`:
```python
class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"  # New channel
```

2. Create new task in `tasks.py`:
```python
@celery_app.task(bind=True, **TASK_RETRY_KWARGS)
def send_whatsapp_notification(self, notification_data: Dict) -> Dict:
    # Implementation
    pass
```

3. Add queue routing in `celery_config.py`:
```python
task_routes={
    'tasks.send_whatsapp_notification': {'queue': 'whatsapp'},
}
```

### Integrating with Real Services

#### Email (AWS SES)
```python
import boto3

ses_client = boto3.client('ses',
    aws_access_key_id=os.getenv('AWS_SES_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SES_SECRET_KEY'),
    region_name=os.getenv('AWS_SES_REGION')
)

ses_client.send_email(
    Source='notifications@airline.com',
    Destination={'ToAddresses': [email]},
    Message={'Subject': {'Data': subject}, 'Body': {'Html': {'Data': body}}}
)
```

#### SMS (Twilio)
```python
from twilio.rest import Client

client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

message = client.messages.create(
    body=sms_text,
    from_=os.getenv('TWILIO_PHONE_NUMBER'),
    to=phone_number
)
```

#### Push (Firebase Cloud Messaging)
```python
import firebase_admin
from firebase_admin import messaging

message = messaging.Message(
    notification=messaging.Notification(title=title, body=body),
    token=push_token
)
response = messaging.send(message)
```

## Monitoring

### Flower Dashboard

Access Flower at http://localhost:5555 to view:
- Active tasks
- Task history
- Worker status
- Queue lengths
- Success/failure rates
- Task execution time

### Logs

Each worker outputs detailed logs showing:
- Tasks received
- Processing status
- Success/failure messages
- Retry attempts

## Production Considerations

### Security
- Use TLS for Valkey connections (rediss://)
- Implement authentication for Valkey
- Store credentials in secure secret management (AWS Secrets Manager, HashiCorp Vault)
- Use environment-specific configuration

### Scalability
- Add more workers to handle increased load
- Use Valkey Cluster for high availability
- Implement rate limiting for external services
- Use connection pooling

### Reliability
- Implement dead letter queues for failed tasks
- Set up monitoring and alerting
- Use task result backends for tracking
- Implement idempotency checks

### Performance
- Optimize worker prefetch multiplier based on task duration
- Use task priorities for important notifications
- Implement caching for frequently accessed data
- Monitor queue depths and scale workers accordingly

## Troubleshooting

### Workers not receiving tasks
- Verify Valkey/Redis is running: `docker ps`
- Check connection URL in `.env`
- Ensure workers are listening to correct queues

### Tasks failing
- Check worker logs for error messages
- Verify Pydantic model validation
- Check external service credentials
- Review retry configuration

### High latency
- Increase number of workers
- Optimize task execution time
- Check Valkey/Redis performance
- Review network connectivity

## Why Valkey?

Valkey is a high-performance, open-source key-value store that's fully compatible with Redis:

- **Open Source**: Community-driven under Linux Foundation
- **High Performance**: Sub-millisecond latency
- **Battle-Tested**: Based on Redis 7.2.4
- **Cost-Effective**: No licensing costs
- **Active Development**: Regular updates and improvements

## Resources

- [Valkey Documentation](https://valkey.io/docs/)
- [Valkey GitHub](https://github.com/valkey-io/valkey)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Flower Documentation](https://flower.readthedocs.io/)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Open an issue on GitHub
- Join the Valkey community discussions
- Check documentation links above
