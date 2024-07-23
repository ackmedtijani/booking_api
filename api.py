import os
import secrets

from datetime import datetime ,  timedelta
from urllib.parse import urlencode
from typing import List

import requests
from beanie import init_beanie , PydanticObjectId
from fastapi import FastAPI, HTTPException , Depends , status , Request
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from database import User , Booking
from schemas import UserCreate , Token , BookingCreate , BookingUpdate , AccessToken
from auth import (authenticate_user ,
                  get_user_by_email,
                    get_password_hash,
                    verify_token,
                  ACCESS_TOKEN_EXPIRE_MINUTES , 
                  REFRESH_TOKEN_EXPIRE_MINUTES,
                  create_access_token,
                  get_current_active_user
                )

app = FastAPI()

print("os client secret" , os.environ.get("GOOGLE_CLIENT_SECRET"))

OAUTH_CONFIG = {
    # Google OAuth 2.0 documentation:
    # https://developers.google.com/identity/protocols/oauth2/web-server#httprest
    'google': {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://accounts.google.com/o/oauth2/token',
        'userinfo': {
            'url': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'email': lambda json: json['email'],
            'profile' : lambda json: json['profile']
        },
        'scopes': ['https://www.googleapis.com/auth/userinfo.email' ,
                   "https://www.googleapis.com/auth/userinfo.profile"],
    },

    # GitHub OAuth 2.0 documentation:
    # https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
    'github': {
        'client_id': os.environ.get('GITHUB_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo': {
            'url': 'https://api.github.com/user/emails',
            'email': lambda json: json[0]['email'],
        },
        'scopes': ['user:email'],
    },
}

@app.on_event("startup")
async def on_startup():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client["booking_api"]
    await init_beanie(database, document_models=[User, Booking])
    
@app.get('/authorize/{provider}')
def oauth2_authorize(request : Request, provider : str):

    provider_data = OAUTH_CONFIG.get(provider)
    if provider_data is None:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, 
                            detail="Auth Provider not available")

    # generate a random string for the state parameter

    # create a query string with all the OAuth2 parameters
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': request.url_for('oauth2_callback', provider=provider,
                                ),
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']),
    })

    # redirect the user to the OAuth2 provider authorization URL
    return {"authorization_url" : provider_data['authorize_url'] + '?' + qs}

@app.get('/callback/{provider}' , response_model=AccessToken)
async def oauth2_callback(provider : str , request : Request , 
                    error : str = None , code : str = None , 
                    ):

    provider_data = OAUTH_CONFIG.get(provider)
    if provider_data is None:
        raise HTTPException(status_code=  status.HTTP_401_UNAUTHORIZED, 
                            detail = {"message" : f"{provider} not available"})

    # if there was an authentication error, flash the error messages and exit
    
    
    if error:
        raise HTTPException(status_code=  status.HTTP_401_UNAUTHORIZED, 
                            detail = {"messsage" : "Error encountered while authenticating" , 
                       "errors" : error})

    # make sure that the state parameter matches the one we created in the
    # authorization request
    
    
    """
    if request.args['state'] != session.get('session_state'):
       return jsonify("session doesn't match") , 401
       
    """

    # make sure that the authorization code is present
    if not code:
         raise HTTPException(status_code=  status.HTTP_401_UNAUTHORIZED, 
                            detail = "Code is misssing")

    print("CLIENT SECREET" , provider_data['client_secret'])
    # exchange the authorization code for an access token
    response = requests.post(provider_data['token_url'], data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': request.url_for('oauth2_callback', provider=provider,
                                ),
    }, headers={'Accept': 'application/json'})
    if response.status_code != 200:
        print("response" , response.text)
        raise HTTPException(status_code=  status.HTTP_401_UNAUTHORIZED, 
                            detail = "Authorization code" 
                       )
        
    oauth2_token = response.json().get('access_token')
    if not oauth2_token:
         raise HTTPException(status_code=  status.HTTP_401_UNAUTHORIZED, 
                            detail = "Oauth token not found")
        
    

    # use the access token to get the user's email address
    response = requests.get(provider_data['userinfo']['url'], headers={
        'Authorization': 'Bearer ' + oauth2_token,
        'Accept': 'application/json',
    })
    if response.status_code != 200:
         raise HTTPException(status_code=  status.HTTP_401_UNAUTHORIZED, 
                            detail = {"messsage" : "Acces code" , 
                       "errors" : error})
    email = provider_data['userinfo']['email'](response.json())
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
    
    
    
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    refresh_token = create_access_token(
        data={'sub' : user.email} , expires_delta = timedelta(REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    print("refrresh" , refresh_token)
    return {"access_token": access_token, "token_type": "bearer" , "refresh_token" : refresh_token}  
            

@app.post("/refresh", response_model=AccessToken)
async def refresh_access_token(refresh_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print("token" , refresh_token)
    payload = verify_token(refresh_token)
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = await get_user_by_email(email)
    if user is None:
        raise credentials_exception
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    
    user = user.dict()
    
    user['password'] = get_password_hash(user['password'])
    
    value = await User.find(User.email == user['email']).to_list()
    if value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST , 
                            "EMAIL allready user")
    
    user_doc = User(**user)
    await user_doc.insert()
    return user_doc

@app.get("/users/", response_model=List[User])
async def get_users():
    users = await User.find_all().to_list()
    return users


@app.post("/bookings/", response_model=Booking)
async def create_booking(
    booking: BookingCreate, current_user: User = Depends(get_current_active_user)
):
    booking_doc = Booking(user_id=current_user.id, **booking.dict())
    await booking_doc.insert()
    return booking_doc

@app.get("/bookings/", response_model=List[Booking])
async def get_bookings(current_user: User = Depends(get_current_active_user)):
    bookings = await Booking.find(Booking.user_id == current_user.id).to_list()
    return bookings

@app.put("/bookings/{booking_id}", response_model=Booking)
async def update_booking(
    booking_id: PydanticObjectId,
    booking: BookingUpdate,
    current_user: User = Depends(get_current_active_user),
):
    
    try:
        booking_doc = await Booking.get(booking_id)
        if not booking_doc or booking_doc.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
            )
        if booking.is_cancelled:
            booking_doc.is_cancelled = True
        else:
            if booking.booking_time:
                booking_doc.booking_time = booking.booking_time
            if booking.end_time:
                if (booking_doc.booking_time and (booking_doc.booking_time > booking.end_time)):
                    raise HTTPException(
                        status_code = status.HTTP_400_BAD_REQUEST , 
                        detail = "Booking time can't be greater than end_time"
                    )
                booking_doc.end_time = booking.end_time
            if booking.description:
                booking_doc.description = booking.description
            if booking.is_recurring is not None:
                if booking_doc.is_recurring is False and booking_doc.end_time is None:
                    raise HTTPException(
                        status_code = status.HTTP_400_BAD_REQUEST , 
                        detail = "Booking can't be false"
                    )
                booking_doc.is_recurring = booking.is_recurring
            if booking.recurrence_interval:
                if (booking_doc.is_recurring is not None and booking_doc.recurrence_interval is None) \
                and (booking_doc.is_recurring is None and booking_doc.recurrence_interval is not None):
                    raise HTTPException(
                        status_code = status.HTTP_400_BAD_REQUEST , 
                        detail = "Booking time can't be greater than end_time"
                        )
                booking_doc.recurrence_interval = booking.recurrence_interval
    
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST , 
                            detail = str(e))     
    

    await booking_doc.save()
    return booking_doc

@app.delete("/bookings/{booking_id}", response_model=dict)
async def cancel_booking(
    booking_id: PydanticObjectId,
    current_user: User = Depends(get_current_active_user),
):
    booking_doc = await Booking.get(booking_id)
    if not booking_doc or booking_doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    booking_doc.is_cancelled = True
    await booking_doc.save()
    return {"message": "Booking cancelled successfully"}

@app.get("/bookings/history", response_model=List[Booking])
async def get_booking_history(current_user: User = Depends(get_current_active_user)):
    bookings = await Booking.find(
        Booking.user_id == current_user.id, Booking.booking_time < datetime.utcnow()
    ).to_list()
    return bookings

@app.get("/bookings/upcoming", response_model=List[Booking])
async def get_upcoming_bookings(current_user: User = Depends(get_current_active_user)):
    bookings = await Booking.find(
        Booking.user_id == current_user.id, Booking.booking_time >= datetime.utcnow()
    ).to_list()
    return bookings

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000 , reload=True)
