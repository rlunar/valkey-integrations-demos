# Building a Real-Time Flight Notification System with Celery and Valkey

As air travel becomes increasingly complex, passengers need timely updates about their flights. In this tutorial, we'll build a robust flight notification system that sends email, SMS, and push notifications when flight statuses change—such as delays, boarding calls, or cancellations.

We'll use **Celery** for task management, **Valkey** (or Redis) as our message broker, and **Pydantic** for data validation. This architecture ensures reliable, asynchronous message processing that can scale with demand.

## Why This Architecture?

- **Celery**: A distributed task queue that handles asynchronous job execution
- **Valkey**: A high-performance key-value store that serves as Celery's message broker (Redis-compatible)
- **Pydantic**: Provides runtime data validation and settings management using Python type annotations

## Prerequisites

```bash
pip install celery redis pydantic python-dotenv
```

You'll also need Valkey or Redis running locally:

```bash
# Using Docker for Valkey
docker run -d --name valkey -p 6379:6379 valkey/valkey:latest
```

## Project Structure

```
flight-notifications/
├── models.py          # Pydantic models
├── tasks.py           # Celery tasks
├── celery_config.py   # Celery configuration
├── main.py            # Application entry point
└── .env               # Environment variables
```

## Step 1: Define Data Models with Pydantic

Let's start by creating our data models. Pydantic ensures that our data is always valid and well-structured.

```python
# models.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Literal, Optional
from datetime import datetime
from enum import Enum

class FlightStatus(str, Enum):
    """Enumeration of possible flight statuses"""
    SCHEDULED = "scheduled"
    DELAYED = "delayed"
    BOARDING = "boarding"
    DEPARTED = "departed"
    CANCELLED = "cancelled"
    ARRIVED = "arrived"

class NotificationType(str, Enum):
    """Types of notifications we can send"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class Passenger(BaseModel):
    """Passenger information model"""
    passenger_id: str = Field(..., description="Unique passenger identifier")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone_number: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    push_token: Optional[str] = Field(None, description="Device push notification token")
    preferred_notifications: list[NotificationType] = Field(
        default=[NotificationType.EMAIL],
        description="Passenger's preferred notification channels"
    )

    @validator('phone_number')
    def validate_phone(cls, v):
        """Ensure phone number is properly formatted"""
        # Remove any spaces or dashes
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "passenger_id": "P123456",
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "phone_number": "+1234567890",
                "push_token": "expo_push_token_abc123",
                "preferred_notifications": ["email", "sms", "push"]
            }
        }

class Flight(BaseModel):
    """Flight information model"""
    flight_number: str = Field(..., pattern=r'^[A-Z]{2}\d{1,4}$')
    airline: str = Field(..., min_length=2, max_length=100)
    origin: str = Field(..., pattern=r'^[A-Z]{3}$', description="IATA airport code")
    destination: str = Field(..., pattern=r'^[A-Z]{3}$', description="IATA airport code")
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: FlightStatus = FlightStatus.SCHEDULED
    gate: Optional[str] = Field(None, pattern=r'^[A-Z]?\d{1,3}[A-Z]?$')
    passengers: list[Passenger] = Field(default_factory=list)

    @validator('scheduled_arrival')
    def arrival_after_departure(cls, v, values):
        """Ensure arrival is after departure"""
        if 'scheduled_departure' in values and v <= values['scheduled_departure']:
            raise ValueError('Arrival must be after departure')
        return v

    @validator('flight_number')
    def validate_flight_number(cls, v):
        """Ensure flight number is uppercase"""
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "flight_number": "AA101",
                "airline": "American Airlines",
                "origin": "JFK",
                "destination": "LAX",
                "scheduled_departure": "2025-11-05T10:00:00",
                "scheduled_arrival": "2025-11-05T13:30:00",
                "status": "scheduled",
                "gate": "B22"
            }
        }

class FlightNotification(BaseModel):
    """Model for flight notification payloads"""
    flight: Flight
    notification_type: NotificationType
    passenger: Passenger
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "flight": Flight.Config.json_schema_extra["example"],
                "notification_type": "email",
                "passenger": Passenger.Config.json_schema_extra["example"],
                "message": "Your flight AA101 is now boarding at gate B22",
                "timestamp": "2025-11-04T09:45:00"
            }
        }
```

## Step 2: Configure Celery

Now let's configure Celery to use Valkey as the message broker and result backend.

```python
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
```

## Step 3: Create Notification Tasks

Let's implement the Celery tasks that will handle sending notifications.

```python
# tasks.py
from celery_config import celery_app
from models import Flight, Passenger, FlightNotification, NotificationType, FlightStatus
from datetime import datetime
from typing import Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Task retry settings
TASK_RETRY_KWARGS = {
    'max_retries': 3,
    'countdown': 5,  # Wait 5 seconds before retry
    'autoretry_for': (Exception,),
}

@celery_app.task(bind=True, **TASK_RETRY_KWARGS)
def send_email_notification(self, notification_data: Dict) -> Dict:
    """
    Send email notification to passenger about flight status
    
    Args:
        notification_data: Dictionary containing notification information
        
    Returns:
        Dict with status and details
    """
    try:
        # Validate data using Pydantic
        notification = FlightNotification(**notification_data)
        
        logger.info(f"Sending email to {notification.passenger.email}")
        logger.info(f"Subject: Flight {notification.flight.flight_number} Update")
        logger.info(f"Message: {notification.message}")
        
        # In production, integrate with services like:
        # - Amazon SES
        # - SendGrid
        # - Mailgun
        
        # Simulated email sending
        email_content = {
            'to': notification.passenger.email,
            'subject': f'Flight {notification.flight.flight_number} - {notification.flight.status.value.title()}',
            'body': format_email_body(notification),
            'sent_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Email sent successfully to {notification.passenger.email}")
        return {
            'status': 'success',
            'notification_type': 'email',
            'passenger_id': notification.passenger.passenger_id,
            'details': email_content
        }
        
    except Exception as exc:
        logger.error(f"Error sending email: {exc}")
        raise self.retry(exc=exc)

@celery_app.task(bind=True, **TASK_RETRY_KWARGS)
def send_sms_notification(self, notification_data: Dict) -> Dict:
    """
    Send SMS notification to passenger about flight status
    
    Args:
        notification_data: Dictionary containing notification information
        
    Returns:
        Dict with status and details
    """
    try:
        notification = FlightNotification(**notification_data)
        
        logger.info(f"Sending SMS to {notification.passenger.phone_number}")
        logger.info(f"Message: {notification.message}")
        
        # In production, integrate with services like:
        # - Amazon SNS
        # - Twilio
        # - Vonage
        
        # Simulated SMS sending
        sms_content = {
            'to': notification.passenger.phone_number,
            'message': format_sms_message(notification),
            'sent_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"SMS sent successfully to {notification.passenger.phone_number}")
        return {
            'status': 'success',
            'notification_type': 'sms',
            'passenger_id': notification.passenger.passenger_id,
            'details': sms_content
        }
        
    except Exception as exc:
        logger.error(f"Error sending SMS: {exc}")
        raise self.retry(exc=exc)

@celery_app.task(bind=True, **TASK_RETRY_KWARGS)
def send_push_notification(self, notification_data: Dict) -> Dict:
    """
    Send push notification to passenger's mobile device
    
    Args:
        notification_data: Dictionary containing notification information
        
    Returns:
        Dict with status and details
    """
    try:
        notification = FlightNotification(**notification_data)
        
        if not notification.passenger.push_token:
            logger.warning(f"No push token for passenger {notification.passenger.passenger_id}")
            return {
                'status': 'skipped',
                'reason': 'no_push_token',
                'passenger_id': notification.passenger.passenger_id
            }
        
        logger.info(f"Sending push notification to device {notification.passenger.push_token[:10]}...")
        
        # In production, integrate with services like:
        # - Firebase Cloud Messaging (FCM)
        # - Apple Push Notification Service (APNS)
        # - Expo Push Notifications
        
        # Simulated push notification
        push_content = {
            'token': notification.passenger.push_token,
            'title': f'Flight {notification.flight.flight_number} Update',
            'body': notification.message,
            'data': {
                'flight_number': notification.flight.flight_number,
                'status': notification.flight.status.value,
                'gate': notification.flight.gate
            },
            'sent_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Push notification sent successfully")
        return {
            'status': 'success',
            'notification_type': 'push',
            'passenger_id': notification.passenger.passenger_id,
            'details': push_content
        }
        
    except Exception as exc:
        logger.error(f"Error sending push notification: {exc}")
        raise self.retry(exc=exc)

@celery_app.task
def notify_passengers(flight_data: Dict, new_status: str) -> Dict:
    """
    Coordinate sending notifications to all passengers on a flight
    
    Args:
        flight_data: Dictionary containing flight information
        new_status: New flight status
        
    Returns:
        Dict with summary of notifications sent
    """
    try:
        flight = Flight(**flight_data)
        flight.status = FlightStatus(new_status)
        
        # Generate appropriate message based on status
        message = generate_status_message(flight)
        
        results = {
            'flight_number': flight.flight_number,
            'status': new_status,
            'passengers_notified': 0,
            'notifications_sent': []
        }
        
        # Send notifications to all passengers based on their preferences
        for passenger in flight.passengers:
            notification_data = {
                'flight': flight.dict(),
                'passenger': passenger.dict(),
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send notifications based on passenger preferences
            for notif_type in passenger.preferred_notifications:
                if notif_type == NotificationType.EMAIL:
                    task = send_email_notification.delay(
                        {**notification_data, 'notification_type': 'email'}
                    )
                elif notif_type == NotificationType.SMS:
                    task = send_sms_notification.delay(
                        {**notification_data, 'notification_type': 'sms'}
                    )
                elif notif_type == NotificationType.PUSH:
                    task = send_push_notification.delay(
                        {**notification_data, 'notification_type': 'push'}
                    )
                
                results['notifications_sent'].append({
                    'passenger_id': passenger.passenger_id,
                    'type': notif_type.value,
                    'task_id': task.id
                })
            
            results['passengers_notified'] += 1
        
        logger.info(f"Initiated notifications for {results['passengers_notified']} passengers on flight {flight.flight_number}")
        return results
        
    except Exception as exc:
        logger.error(f"Error coordinating passenger notifications: {exc}")
        raise

# Helper functions for message formatting

def format_email_body(notification: FlightNotification) -> str:
    """Format email body with HTML"""
    return f"""
    <html>
        <body>
            <h2>Flight Update for {notification.flight.flight_number}</h2>
            <p>Dear {notification.passenger.first_name} {notification.passenger.last_name},</p>
            
            <p>{notification.message}</p>
            
            <h3>Flight Details:</h3>
            <ul>
                <li><strong>Flight:</strong> {notification.flight.airline} {notification.flight.flight_number}</li>
                <li><strong>Route:</strong> {notification.flight.origin} → {notification.flight.destination}</li>
                <li><strong>Status:</strong> {notification.flight.status.value.title()}</li>
                <li><strong>Scheduled Departure:</strong> {notification.flight.scheduled_departure}</li>
                {f'<li><strong>Gate:</strong> {notification.flight.gate}</li>' if notification.flight.gate else ''}
            </ul>
            
            <p>Thank you for choosing {notification.flight.airline}.</p>
        </body>
    </html>
    """

def format_sms_message(notification: FlightNotification) -> str:
    """Format concise SMS message"""
    gate_info = f" at gate {notification.flight.gate}" if notification.flight.gate else ""
    return f"{notification.flight.airline} {notification.flight.flight_number}: {notification.message}{gate_info}"

def generate_status_message(flight: Flight) -> str:
    """Generate appropriate message based on flight status"""
    messages = {
        FlightStatus.DELAYED: f"Your flight has been delayed. New departure time will be announced shortly.",
        FlightStatus.BOARDING: f"Your flight is now boarding at gate {flight.gate}. Please proceed to the gate.",
        FlightStatus.CANCELLED: f"We regret to inform you that your flight has been cancelled. Please contact customer service for rebooking.",
        FlightStatus.DEPARTED: f"Your flight has departed and is en route to {flight.destination}.",
        FlightStatus.ARRIVED: f"Your flight has arrived at {flight.destination}. Welcome!"
    }
    return messages.get(flight.status, f"Flight status updated to {flight.status.value}")
```

## Step 4: Create the Main Application

Now let's create a script to demonstrate the system in action.

```python
# main.py
from models import Flight, Passenger, FlightStatus, NotificationType
from tasks import notify_passengers
from datetime import datetime, timedelta
import time

def create_sample_flight():
    """Create a sample flight with passengers"""
    
    # Create passengers
    passengers = [
        Passenger(
            passenger_id="P001",
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@example.com",
            phone_number="+1234567890",
            push_token="expo_token_alice123",
            preferred_notifications=[NotificationType.EMAIL, NotificationType.SMS, NotificationType.PUSH]
        ),
        Passenger(
            passenger_id="P002",
            first_name="Bob",
            last_name="Smith",
            email="bob.smith@example.com",
            phone_number="+1987654321",
            preferred_notifications=[NotificationType.EMAIL, NotificationType.PUSH]
        ),
        Passenger(
            passenger_id="P003",
            first_name="Carol",
            last_name="Williams",
            email="carol.williams@example.com",
            phone_number="+1122334455",
            push_token="expo_token_carol456",
            preferred_notifications=[NotificationType.SMS]
        )
    ]
    
    # Create flight
    now = datetime.utcnow()
    flight = Flight(
        flight_number="AA101",
        airline="American Airlines",
        origin="JFK",
        destination="LAX",
        scheduled_departure=now + timedelta(hours=2),
        scheduled_arrival=now + timedelta(hours=7, minutes=30),
        status=FlightStatus.SCHEDULED,
        gate="B22",
        passengers=passengers
    )
    
    return flight

def simulate_flight_events():
    """Simulate various flight status changes"""
    
    print("=" * 60)
    print("Flight Notification System Demo")
    print("Using Celery + Valkey/Redis")
    print("=" * 60)
    
    flight = create_sample_flight()
    
    print(f"\nFlight {flight.flight_number} created")
    print(f"Route: {flight.origin} → {flight.destination}")
    print(f"Passengers: {len(flight.passengers)}")
    print(f"Departure: {flight.scheduled_departure}")
    
    # Simulate flight status changes
    events = [
        (FlightStatus.DELAYED, 2),
        (FlightStatus.BOARDING, 3),
        (FlightStatus.DEPARTED, 2),
    ]
    
    for status, wait_time in events:
        print(f"\n{'=' * 60}")
        print(f"Simulating status change: {status.value.upper()}")
        print(f"{'=' * 60}")
        
        # Update flight status and notify passengers
        result = notify_passengers.delay(
            flight.dict(),
            status.value
        )
        
        print(f"Task ID: {result.id}")
        print(f"Waiting for notifications to be sent...")
        
        # Wait for task to complete
        task_result = result.get(timeout=30)
        
        print(f"\nNotification Summary:")
        print(f"  Passengers notified: {task_result['passengers_notified']}")
        print(f"  Total notifications: {len(task_result['notifications_sent'])}")
        
        for notif in task_result['notifications_sent']:
            print(f"    - {notif['type'].upper()}: Passenger {notif['passenger_id']} (Task: {notif['task_id'][:8]}...)")
        
        print(f"\nWaiting {wait_time} seconds before next event...")
        time.sleep(wait_time)
    
    print(f"\n{'=' * 60}")
    print("Demo completed!")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    simulate_flight_events()
```

## Step 5: Environment Configuration

Create a `.env` file for your configuration:

```bash
# .env
VALKEY_URL=redis://localhost:6379/0

# In production, add your service credentials:
# AWS_SES_ACCESS_KEY=your_key
# AWS_SES_SECRET_KEY=your_secret
# TWILIO_ACCOUNT_SID=your_sid
# TWILIO_AUTH_TOKEN=your_token
# FCM_SERVER_KEY=your_fcm_key
```

## Running the System

### 1. Start Valkey/Redis

```bash
docker run -d --name valkey -p 6379:6379 valkey/valkey:latest
```

### 2. Start Celery Workers

Open multiple terminal windows to start workers for different queues:

```bash
# Terminal 1: Email queue worker
celery -A celery_config worker --loglevel=info -Q email -n email_worker@%h

# Terminal 2: SMS queue worker
celery -A celery_config worker --loglevel=info -Q sms -n sms_worker@%h

# Terminal 3: Push notification queue worker
celery -A celery_config worker --loglevel=info -Q push -n push_worker@%h
```

### 3. Run the Demo

```bash
python main.py
```

## Monitoring with Flower

Install and run Flower to monitor your Celery tasks in real-time:

```bash
pip install flower
celery -A celery_config flower --port=5555
```

Visit `http://localhost:5555` to see:
- Active tasks
- Task history
- Worker status
- Queue lengths
- Task success/failure rates

## Architecture Benefits

### 1. **Scalability**
- Add more workers to handle increased load
- Different queues can scale independently
- Valkey handles millions of messages per second

### 2. **Reliability**
- Tasks are retried automatically on failure
- Messages persist in Valkey until acknowledged
- Dead letter queues for failed tasks

### 3. **Flexibility**
- Easy to add new notification channels
- Passenger preferences control delivery
- Status-based routing and prioritization

### 4. **Type Safety**
- Pydantic validates all data at runtime
- Prevents invalid data from entering the system
- Auto-generates documentation from models

## Production Considerations

### 1. **Security**
```python
# Use TLS for Valkey connections
VALKEY_URL = 'rediss://username:password@valkey-host:6380/0'

# Implement proper authentication
celery_app.conf.update(
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': '/path/to/ca-cert.pem',
        'ssl_certfile': '/path/to/client-cert.pem',
        'ssl_keyfile': '/path/to/client-key.pem',
    }
)
```

### 2. **Monitoring & Alerting**
- Use Flower or Celery Events for real-time monitoring
- Set up CloudWatch/Prometheus metrics
- Alert on high queue depths or task failures

### 3. **Rate Limiting**
```python
@celery_app.task(bind=True, rate_limit='100/m')  # 100 tasks per minute
def send_email_notification(self, notification_data: Dict):
    # Task implementation
    pass
```

### 4. **Message Deduplication**
```python
from celery.utils.time import maybe_make_aware
from datetime import datetime, timedelta

@celery_app.task(bind=True)
def send_notification_once(self, notification_data: Dict):
    """Ensure notification is sent only once using Valkey"""
    from redis import Redis
    
    redis_client = Redis.from_url(VALKEY_URL)
    key = f"notification:{notification_data['passenger']['passenger_id']}:{notification_data['flight']['flight_number']}"
    
    # Set key with 1-hour expiration
    if redis_client.set(key, '1', ex=3600, nx=True):
        # Key didn't exist, send notification
        return send_email_notification(notification_data)
    else:
        # Notification already sent
        return {'status': 'duplicate', 'skipped': True}
```

### 5. **Graceful Degradation**
```python
@celery_app.task(bind=True)
def send_notification_with_fallback(self, notification_data: Dict):
    """Try primary service, fallback to secondary if it fails"""
    try:
        return send_via_primary_service(notification_data)
    except Exception as primary_exc:
        logger.warning(f"Primary service failed: {primary_exc}")
        try:
            return send_via_fallback_service(notification_data)
        except Exception as fallback_exc:
            logger.error(f"Fallback service also failed: {fallback_exc}")
            raise
```

## Why Valkey?

Valkey is a high-performance, open-source key-value store that's fully compatible with Redis. Key benefits:

- **Open Source**: Community-driven development under the Linux Foundation
- **High Performance**: Sub-millisecond latency for most operations
- **Battle-Tested**: Based on Redis 7.2.4, used in production by major companies
- **Cost-Effective**: No licensing costs, reduce infrastructure expenses
- **Vibrant Community**: Active development and community support

## Extending the System

### Add Priority Queues
```python
# High priority for VIP passengers
@celery_app.task(queue='vip_notifications', priority=9)
def send_vip_notification(notification_data: Dict):
    pass
```

### Implement Notification Preferences
```python
class NotificationPreference(BaseModel):
    min_delay_minutes: int = 30  # Only notify for delays > 30 min
    quiet_hours_start: int = 22  # Don't send between 10 PM
    quiet_hours_end: int = 7     # and 7 AM
    language: str = "en"
```

### Add Analytics
```python
@celery_app.task
def track_notification_metrics(notification_data: Dict):
    """Store metrics in Valkey for analytics"""
    from redis import Redis
    
    redis_client = Redis.from_url(VALKEY_URL)
    date_key = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Increment counters
    redis_client.hincrby(f"metrics:{date_key}", "total_notifications", 1)
    redis_client.hincrby(f"metrics:{date_key}", 
                        f"{notification_data['notification_type']}_sent", 1)
```

## Conclusion

We've built a production-ready flight notification system that demonstrates:

✅ **Asynchronous task processing** with Celery  
✅ **High-performance message brokering** with Valkey  
✅ **Type-safe data validation** with Pydantic  
✅ **Scalable architecture** for real-world applications  
✅ **Multiple notification channels** (Email, SMS, Push)  

This architecture can handle thousands of flights and millions of passengers, making it suitable for airlines, travel apps, and booking platforms.

## Resources

- [Valkey Documentation](https://valkey.io/docs/)
- [Valkey GitHub](https://github.com/valkey-io/valkey)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Get Involved

Join the Valkey community:
- 🌟 Star us on [GitHub](https://github.com/valkey-io/valkey)
- 💬 Join discussions on our community forums
- 🐛 Report issues or contribute code
- 📝 Share your Valkey stories

---

*Have questions or want to share your implementation? Reach out to the Valkey community!*
