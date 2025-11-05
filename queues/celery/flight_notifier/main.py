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
        id="AF249",
        airline="France Air 🇫🇷",
        departure_airport="CDG",
        arrival_airport="BER",
        status="DELAYED ⌛",
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
        id="GA006",
        airline="Deutsche Flughafen 🇩🇪",
        departure_airport="BER",
        arrival_airport="MRS",
        status="BOARDING ✈️",
    )
    process_flight_status_update.delay(boarding_flight.model_dump())
    print("Flight API: Boarding task sent. Main app is free.")


if __name__ == "__main__":
    import time
    trigger_flight_delay()
    # Wait a moment and trigger another one
    time.sleep(1)
    trigger_flight_boarding()
