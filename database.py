from datetime import datetime
from typing import Optional

from beanie import Document , PydanticObjectId
from pydantic import EmailStr , Field  , model_validator

class User(Document):
    username: str = Field(..., max_length=50)
    email: EmailStr
    password : str = Field(..., max_length = 250)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        collection = "users"
        

class Booking(Document):
    user_id: PydanticObjectId
    date_of_booking : datetime = Field(default_factory=datetime.utcnow)
    booking_time: datetime
    end_time: Optional[datetime] = None
    description: str = Field(..., max_length=255)
    is_recurring: bool = False
    recurrence_interval: Optional[str] = None  # e.g., "daily", "weekly"
    is_cancelled: bool = False

    class Settings:
        collection = "bookings"