from datetime import datetime
from typing import Optional

from pydantic import BaseModel , EmailStr , Field , model_validator , ValidationError

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password : str
    
    
    
class BookingCreate(BaseModel):
    booking_time: datetime
    end_time: Optional[datetime] = None
    description: str = Field(..., max_length=255)
    is_recurring: bool = False
    recurrence_interval: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_model(self):
        if self.booking_time < datetime.utcnow():
            raise ValueError("Booking time can't be now")
        
        
        if self.is_recurring is False and self.end_time is None:
            raise ValueError("Non reoccuring event has to have an endtime")
        
        if (self.is_recurring is not None and self.recurrence_interval is None) \
            and (self.is_recurring is None and self.recurrence_interval is not None):
                raise ValueError("Is recurring and recurrence_interval have to be false and None respectively and vice versa. ")
        
        if self.end_time and (self.booking_time > self.end_time):
            raise ValueError("End time can't be lesser than booking time")
        return self

class BookingUpdate(BaseModel):
    booking_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_interval: Optional[str] = None
    is_cancelled: Optional[bool] = None
    
    @model_validator(mode='after')
    def validate_model(self):
        if self.booking_time and self.booking_time < datetime.utcnow():
            raise ValueError("Booking time can't be now")
        
        
        if self.is_recurring is False and self.end_time is None:
            raise ValueError("Non reoccuring event has to have an endtime")
        
        if (self.is_recurring is not None and self.recurrence_interval is None) \
            and (self.is_recurring is None and self.recurrence_interval is not None):
                raise ValueError("Is recurring and recurrence_interval have to be false and None respectively and vice versa. ")
        
        if self.end_time and (self.booking_time and self.booking_time > self.end_time):
            raise ValueError("End time can't be lesser than booking time")
        return self
    
    
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token : Optional[str] = None
    
class AccessToken(BaseModel):
    access_token : str
    token_type : str

class TokenData(BaseModel):
    email: Optional[str] = None


    
    