# tasks.py
import time
from celery import Celery
from models import Passenger, Flight  # Import our Pydantic models

# 1. Configure Celery
# We point it to our Valkey instance as the broker.
# The 'backend' is also Valkey; this is used to store task results.
app = Celery(
    "flight_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6380/0",
)

# Optional: Improve Celery's Pydantic integration
# This tells Celery to trust our Pydantic models for serialization.
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


# 2. Define our individual "worker" tasks


@app.task(name="notifications.send_email")
def send_email(passenger_data: dict, message: str):
    """
    Simulates sending an email to a passenger.
    """
    # Deserialize the dictionary back into our Pydantic model
    passenger = Passenger(**passenger_data)
    print(f"\n[📧 EMAIL TASK]... Initiating email send to {passenger.email}")
    # Simulate a network call to an email API (e.g., SendGrid, Mailgun)
    time.sleep(2)  # Simulate 1-second API call
    print(f"[📧 EMAIL TASK]... ✅ SUCCESS: Sent '{message}' to {passenger.name} ({passenger.email})")
    return f"📧 Email sent to {passenger.email}"


@app.task(name="notifications.send_sms")
def send_sms(passenger_data: dict, message: str):
    """
    Simulates sending an SMS to a passenger.
    """
    passenger = Passenger(**passenger_data)
    print(f"\n[📱 SMS TASK]... Initiating SMS send to {passenger.phone_number}")
    # Simulate a network call to an SMS gateway (e.g., Twilio)
    time.sleep(3)  # Simulate a SLOW 3-second API call
    print(f"[📱 SMS TASK]... ✅ SUCCESS: Sent '{message}' to {passenger.name} ({passenger.phone_number})")
    return f"📱 SMS sent to {passenger.phone_number}"


@app.task(name="notifications.send_push_notification")
def send_push_notification(passenger_data: dict, message: str):
    """
    Simulates sending a push notification.
    """
    passenger = Passenger(**passenger_data)
    if not passenger.push_token:
        print(f"\n[📳 PUSH TASK]... ⏩ SKIPPED: Passenger {passenger.name} has no push token.")
        return "No push token"
    print(f"\n[📳 PUSH TASK]... Initiating push notification to token {passenger.push_token}")
    # Simulate a network call (e.g., to APNS or Firebase)
    time.sleep(1.5)  # Push notifications are usually fast
    print(f"[📳 PUSH TASK]... ✅ SUCCESS: Sent '{message}' to {passenger.name} (token: {passenger.push_token[:10]}...)")
    return f"📳 Push sent to {passenger.push_token}"


# 3. Define our "main" task that fans out the work


@app.task(name="notifications.process_flight_status_update")
def process_flight_status_update(flight_data: dict):
    """
    This is the main task that a flight API would call.
    It finds all passengers and triggers the individual notification tasks.
    """
    flight = Flight(**flight_data)
    print(f"\n--- PROCESSING ⚙️ flight {flight.id} status change: {flight.status} ---")
    # --- In a real app, you would fetch this from your database ---
    # We'll mock this data for the demo.
    mock_passengers = [
        Passenger(
            id=1,
            name="Jane Doe 👩",
            email="jane@example.com",
            phone_number="+1555123456",
            push_token="push-token-jane-abc",
        ),
        Passenger(
            id=2,
            name="John Doe 👱‍♂️",
            email="john@example.com",
            phone_number="+1555654321",
            push_token=None,
        ),  # John doesn't get push notifications
    ]
    # --- End of mock data ---
    message = f"🛩️ Flight {flight.id} update: Your flight status is now {flight.status}."
    # Fan out the work!
    # We call .delay() on each sub-task to send it to the Celery queue.
    for passenger in mock_passengers:
        # We pass the Pydantic model as a dict, as it's easier to serialize.
        passenger_dict = passenger.model_dump()
        send_email.delay(passenger_dict, message)
        send_sms.delay(passenger_dict, message)
        send_push_notification.delay(passenger_dict, message)
    print(f"--- ☑️ All notifications for flight {flight.id} have been queued. ---")
