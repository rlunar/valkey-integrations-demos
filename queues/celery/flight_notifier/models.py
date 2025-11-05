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
    push_token: Optional[str] = None  # Not all users have push enabled


class Flight(BaseModel):
    """
    Defines a flight and its current status.
    """
    id: str  # e.g., "BA249"
    airline: str
    departure_airport: str
    arrival_airport: str
    status: str  # e.g., "ON_TIME", "DELAYED", "CANCELLED", "BOARDING"
