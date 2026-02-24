# main.py
from models import Flight, Passenger, FlightStatus, NotificationType
from tasks import notify_passengers
from datetime import datetime, timedelta
import time

def create_sample_flight():
    """Create a sample flight with passengers"""
    
    # Create passengers with different notification preferences
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
        ),
        Passenger(
            passenger_id="P004",
            first_name="David",
            last_name="Brown",
            email="david.brown@example.com",
            phone_number="+1555666777",
            push_token="expo_token_david789",
            preferred_notifications=[NotificationType.EMAIL, NotificationType.SMS, NotificationType.PUSH]
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
    
    print("=" * 70)
    print(" " * 15 + "FLIGHT NOTIFICATION SYSTEM DEMO")
    print(" " * 20 + "Using Celery + Valkey/Redis")
    print("=" * 70)
    
    flight = create_sample_flight()
    
    print(f"\n✈️  Flight {flight.flight_number} created")
    print(f"    Airline: {flight.airline}")
    print(f"    Route: {flight.origin} → {flight.destination}")
    print(f"    Passengers: {len(flight.passengers)}")
    print(f"    Scheduled Departure: {flight.scheduled_departure.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"    Gate: {flight.gate}")
    
    print(f"\n📋 Passenger Notification Preferences:")
    for passenger in flight.passengers:
        prefs = ", ".join([p.value.upper() for p in passenger.preferred_notifications])
        print(f"    • {passenger.first_name} {passenger.last_name}: {prefs}")
    
    # Simulate flight status changes
    events = [
        (FlightStatus.DELAYED, 3, "⏰"),
        (FlightStatus.BOARDING, 4, "🚪"),
        (FlightStatus.DEPARTED, 2, "🛫"),
    ]
    
    for status, wait_time, emoji in events:
        print(f"\n{'=' * 70}")
        print(f"{emoji}  Simulating status change: {status.value.upper()}")
        print(f"{'=' * 70}")
        
        # Update flight status and notify passengers
        print(f"\n📤 Dispatching notification tasks to Celery workers...")
        result = notify_passengers.delay(
            flight.dict(),
            status.value
        )
        
        print(f"    Task ID: {result.id}")
        print(f"    Waiting for notifications to be processed...")
        
        # Wait for task to complete
        try:
            task_result = result.get(timeout=30)
            
            print(f"\n✅ Notification Summary:")
            print(f"    Passengers notified: {task_result['passengers_notified']}")
            print(f"    Total notifications queued: {len(task_result['notifications_sent'])}")
            
            # Group notifications by type
            notif_by_type = {}
            for notif in task_result['notifications_sent']:
                notif_type = notif['type']
                if notif_type not in notif_by_type:
                    notif_by_type[notif_type] = []
                notif_by_type[notif_type].append(notif)
            
            print(f"\n    Breakdown by channel:")
            for notif_type, notifs in notif_by_type.items():
                print(f"      {notif_type.upper()}: {len(notifs)} notifications")
                for notif in notifs:
                    print(f"        └─ Passenger {notif['passenger_id']} (Task: {notif['task_id'][:12]}...)")
            
            print(f"\n⏳ Waiting {wait_time} seconds before next event...")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"\n❌ Error processing notifications: {e}")
            print(f"    Make sure Celery workers are running!")
            break
    
    print(f"\n{'=' * 70}")
    print(" " * 25 + "✅ DEMO COMPLETED!")
    print(f"{'=' * 70}")
    print(f"\n📊 Check Flower at http://localhost:5555 to monitor task execution")
    print(f"💡 Check Celery worker logs to see detailed notification processing\n")

if __name__ == "__main__":
    try:
        simulate_flight_events()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running demo: {e}")
        print("Make sure:")
        print("  1. Valkey/Redis is running on port 6379")
        print("  2. Celery workers are started")
        print("  3. All dependencies are installed (pip install -r requirements.txt)")
