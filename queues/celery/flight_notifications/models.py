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
