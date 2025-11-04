# ✈️ Take Flight: Building a Real-Time Flight Notification System with Celery, Pydantic, and Valkey

As developers, we're often tasked with building systems that react to real-time events. One of the most common and critical use cases is a notification system. When a user's flight is delayed, canceled, or boarding, they expect to know *immediately*.

Handling this "in-band" (e.g., during a web request) is a recipe for disaster. A single slow API call to an SMS gateway could freeze your application. The solution is to move this work "out-of-band" using a distributed task queue.

In this tutorial, we'll build a robust flight notification system using:

  * **Python:** Our development language.
  * **Celery:** The leading distributed task queue framework for Python.
  * **Valkey:** A high-performance, in-memory data store that will act as our message broker.
  * **Pydantic:** A data validation library to ensure our data (for passengers and flights) is clean and strongly typed.

We'll build a system that can take a flight status update (like "DELAYED") and fan out notifications to all affected passengers via email, SMS, and push notification.

### Prerequisites

Before we start, make sure you have:

  * **Python 3.8+** installed.
  * A **Valkey server** running. If you have Docker, the easiest way is `docker run -d -p 6379:6379 valkey:latest`. Otherwise, you can install it locally via a package manager.
  * Basic understanding of Python virtual environments.

### Step 1: Setting Up Your Environment

Let's create a project directory, set up a virtual environment, and install our libraries.

Create and enter the project directory
```bash
mkdir flight_notifier
cd flight_notifier
```

Create a virtual environment
```bash
uv init -q
```

Install our dependencies
```bash
uv add celery redis pydantic
```

```bash
uv add "pydantic[email]"
```

-----

### Step 2: Modeling Our Data with Pydantic

Clear data models are the foundation of a good application. We'll use Pydantic to define what a `Passenger` and a `Flight` look like. This helps Celery serialize/deserialize the data and ensures our tasks always receive the data they expect.

Create a file named `models.py`:

```python
# models.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class Passenger(BaseModel):
    """
    Defines a passenger with contact info.
    """
    id: int
    name: str
    email: EmailStr
    phone_number: str
    push_token: Optional[str] = None # Not all users have push enabled

class Flight(BaseModel):
    """
    Defines a flight and its current status.
    """
    id: str  # e.g., "BA249"
    airline: str
    departure_airport: str
    arrival_airport: str
    status: str  # e.g., "ON_TIME", "DELAYED", "CANCELLED", "BOARDING"
```

These models are simple, readable, and provide free data validation.

-----

### Step 3: Configuring Celery and Defining Tasks

This is the core of our system. We'll create a `tasks.py` file to configure Celery and define all our individual notification tasks.

Celery needs a "broker" to pass messages between your main application and your workers. We'll tell Celery to use our local Valkey server for this.

Create a file named `tasks.py`:

```python
# tasks.py
import time
from celery import Celery
from models import Passenger, Flight # Import our Pydantic models

# 1. Configure Celery
# We point it to our Valkey instance as the broker.
# The 'backend' is also Valkey; this is used to store task results.
app = Celery(
    'flight_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Optional: Improve Celery's Pydantic integration
# This tells Celery to trust our Pydantic models for serialization.
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
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
    print(f"\n[EMAIL TASK]... Initiating email send to {passenger.email}")

    # Simulate a network call to an email API (e.g., SendGrid, Mailgun)
    time.sleep(1) # Simulate 1-second API call

    print(f"[EMAIL TASK]... SUCCESS: Sent '{message}' to {passenger.name} ({passenger.email})")
    return f"Email sent to {passenger.email}"


@app.task(name="notifications.send_sms")
def send_sms(passenger_data: dict, message: str):
    """
    Simulates sending an SMS to a passenger.
    """
    passenger = Passenger(**passenger_data)
    print(f"\n[SMS TASK]... Initiating SMS send to {passenger.phone_number}")

    # Simulate a network call to an SMS gateway (e.g., Twilio)
    time.sleep(3) # Simulate a SLOW 3-second API call

    print(f"[SMS TASK]... SUCCESS: Sent '{message}' to {passenger.name} ({passenger.phone_number})")
    return f"SMS sent to {passenger.phone_number}"


@app.task(name="notifications.send_push_notification")
def send_push_notification(passenger_data: dict, message: str):
    """
    Simulates sending a push notification.
    """
    passenger = Passenger(**passenger_data)
    if not passenger.push_token:
        print(f"\n[PUSH TASK]... SKIPPED: Passenger {passenger.name} has no push token.")
        return "No push token"

    print(f"\n[PUSH TASK]... Initiating push notification to token {passenger.push_token}")

    # Simulate a network call (e.g., to APNS or Firebase)
    time.sleep(0.5) # Push notifications are usually fast

    print(f"[PUSH TASK]... SUCCESS: Sent '{message}' to {passenger.name} (token: {passenger.push_token[:10]}...)")
    return f"Push sent to {passenger.push_token}"


# 3. Define our "main" task that fans out the work

@app.task(name="notifications.process_flight_status_update")
def process_flight_status_update(flight_data: dict):
    """
    This is the main task that a flight API would call.
    It finds all passengers and triggers the individual notification tasks.
    """
    flight = Flight(**flight_data)
    print(f"\n--- PROCESSING flight {flight.id} status change: {flight.status} ---")

    # --- In a real app, you would fetch this from your database ---
    # We'll mock this data for the demo.
    mock_passengers = [
        Passenger(id=1, name="Alice Smith", email="alice@example.com", phone_number="+1555123456", push_token="push-token-alice-abc"),
        Passenger(id=2, name="Bob Johnson", email="bob@example.com", phone_number="+1555654321", push_token=None), # Bob doesn't get push notifications
    ]
    # --- End of mock data ---

    message = f"Flight {flight.id} update: Your flight status is now {flight.status}."

    # Fan out the work!
    # We call .delay() on each sub-task to send it to the Celery queue.
    for passenger in mock_passengers:
        # We pass the Pydantic model as a dict, as it's easier to serialize.
        passenger_dict = passenger.model_dump()

        send_email.delay(passenger_dict, message)
        send_sms.delay(passenger_dict, message)
        send_push_notification.delay(passenger_dict, message)

    print(f"--- All notifications for flight {flight.id} have been queued. ---")

```

Note the `send_sms` task has an artificial 3-second delay. In a traditional app, this would block everything. In our Celery app, it will just be a slow task that one of our workers handles without blocking any other notifications.

-----

### Step 4: Creating the "Producer" Application

Now we need a script to *trigger* these tasks. This would be your main web application (e.g., a Django or Flask API) that detects a flight status change.

For our demo, we'll just make a simple script called `main.py`.

Create `main.py`:

```python
# main.py
from tasks import process_flight_status_update
from models import Flight

def trigger_flight_delay():
    """
    Simulates a flight being delayed.
    """
    print("Flight API: Detected status change for BA249. Triggering tasks...")

    # 1. Create our flight data
    delayed_flight = Flight(
        id="BA249",
        airline="British Airways",
        departure_airport="LHR",
        arrival_airport="JFK",
        status="DELAYED"
    )

    # 2. Send the main task to the Celery queue
    # We use .delay() to execute the task asynchronously.
    # We must pass Pydantic models as dictionaries (.model_dump())
    process_flight_status_update.delay(delayed_flight.model_dump())

    print("Flight API: Task has been sent to the queue. Main app is free to do other work.")


def trigger_flight_boarding():
    """
    Simulates a flight starting to board.
    """
    print("\nFlight API: Detected status change for AF006. Triggering tasks...")

    boarding_flight = Flight(
        id="AF006",
        airline="Air France",
        departure_airport="CDG",
        arrival_airport="SFO",
        status="BOARDING"
    )

    process_flight_status_update.delay(boarding_flight.model_dump())
    print("Flight API: Boarding task sent. Main app is free.")


if __name__ == "__main__":
    trigger_flight_delay()

    # Wait a moment and trigger another one
    import time
    time.sleep(2)
    trigger_flight_boarding()
```

-----

### Step 5: Running the System\!

This is the fun part. We need three separate terminals.

**➡️ Terminal 1: Start your Valkey Broker**
If you haven't already, get your Valkey server running.

```bash
# (If using Docker)
docker run -d -p 6379:6379 redis:latest
```

**➡️ Terminal 2: Start your Celery Worker**
Activate your virtual environment and tell Celery to start listening for tasks from the `tasks.py` file.

```bash
# Make sure your venv is active
source venv/bin/activate

# Start the worker
# -A tasks: Look for the Celery app in the 'tasks.py' file
# --loglevel=info: Show us what's happening
celery -A tasks worker --loglevel=info
```

You will see the worker connect to Valkey and report that it's ready to receive tasks.

**➡️ Terminal 3: Run the Producer**
Now, let's simulate the flight status changes. Open a third terminal, activate your virtual environment, and run `main.py`.

```bash
# Make sure your venv is active
source venv/bin/activate

# Run the script
python main.py
```

**Watch the magic happen\!**

In **Terminal 3 (Producer)**, you'll see it finish almost instantly:

```
Flight API: Detected status change for BA249. Triggering tasks...
Flight API: Task has been sent to the queue. Main app is free to do other work.

Flight API: Detected status change for AF006. Triggering tasks...
Flight API: Boarding task sent. Main app is free.
```

Now look at **Terminal 2 (Worker)**. You'll see it spring to life, picking up all the tasks. It will process the fast ones (email, push) and the slow ones (SMS) *in parallel* without blocking.

```
[WORKER LOGS]
...
[... INFO/MainProcess] Received task: notifications.process_flight_status_update[...]
[... INFO/MainProcess] Received task: notifications.process_flight_status_update[...]
...
--- PROCESSING flight BA249 status change: DELAYED ---
--- All notifications for flight BA249 have been queued. ---
[... INFO/MainProcess] Task notifications.process_flight_status_update[...] succeeded
--- PROCESSING flight AF006 status change: BOARDING ---
--- All notifications for flight AF006 have been queued. ---
[... INFO/MainProcess] Task notifications.process_flight_status_update[...] succeeded
...
[... INFO/ForkPoolWorker-1] Task notifications.send_email[...] received
[... INFO/ForkPoolWorker-2] Task notifications.send_sms[...] received
[... INFO/ForkPoolWorker-3] Task notifications.send_push_notification[...] received
[... INFO/ForkPoolWorker-4] Task notifications.send_email[...] received
...
[PUSH TASK]... Initiating push notification to token push-token-alice-abc
[PUSH TASK]... SUCCESS: Sent 'Flight BA249...' to Alice Smith...
[... INFO/ForkPoolWorker-3] Task notifications.send_push_notification[...] succeeded
...
[EMAIL TASK]... Initiating email send to alice@example.com
[EMAIL TASK]... SUCCESS: Sent 'Flight BA249...' to Alice Smith...
[... INFO/ForkPoolWorker-1] Task notifications.send_email[...] succeeded
...
[SMS TASK]... Initiating SMS send to +1555123456
[SMS TASK]... SUCCESS: Sent 'Flight BA249...' to Alice Smith...
[... INFO/ForkPoolWorker-2] Task notifications.send_sms[...] succeeded (took 3.01s)
```

Even though the SMS task took 3 seconds, it didn't stop the email or push notifications from going out immediately. That's the power of asynchronous task queues\!

### Conclusion

We've successfully built a scalable, resilient notification system. By decoupling our slow, I/O-bound tasks (like sending emails or SMS) from our main application, we've made our app faster and more reliable.

  * **Celery** provided the framework for defining, sending, and executing tasks.
  * **Pydantic** ensured our data was valid and easy to work with.
  * **Valkey** acted as the high-speed, reliable broker that connects our application to our workers.

-----

### ⭐ Bonus for Open Source Advocates: Swapping to Valkey

As a Developer Advocate for open source Valkey, you'll be happy to know how easy it is to migrate this entire application.

**Valkey is a drop-in replacement for Redis.** Because it maintains compatibility with the Redis 7.2 API, Celery's Redis client works with Valkey out of the box.

To switch this project from Redis to Valkey, you would:

1.  **Run Valkey:** Stop your Redis server and start your Valkey server (e.g., `docker run -d -p 6379:6379 valkey/valkey` or `valkey-server`).

2.  **Update your Broker URL:** In `tasks.py`, simply change the protocol in your broker and backend URLs:

    ```python
    # tasks.py (with Valkey)

    app = Celery(
        'flight_tasks',
        broker='valkey://localhost:6379/0',
        backend='valkey://localhost:6379/0'
    )
    ```

3.  **Install the Valkey driver (Good Practice):** While Celery's `redis` dependency will likely work, the best practice is to use the official Valkey Python client.

    ```bash
    pip uninstall redis
    pip install valkey
    ```

    Celery's Redis broker transport will automatically detect and use the `valkey` library if it's installed.

That's it\! You've just migrated your entire task queue to Valkey, gaining all the benefits of its open source, community-driven development without changing your application code.
