Booking API for booking appointments. 

## Set Up

Clone to repository to where platform you want to deploy the API to. 

### Dependencies
Set up dependencies by running this command: `pip install -r requirements.txt` which installs the dependencies from the `requirements.txt` file. 

### Environment Variables
Add a `.env` file to the directory. 
The `.env` file should include variables such as the `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `SECRET_KEY`. 

### Running the Application

To run the application, run this command. `python api.py`. 


## API Endpoints and Functionalities. 

### Authentication and User Management Endpoints.

#### User Creation
Endpoint: `/users`
Method: `POST`
Content-Type: `application/json`
payload: username, password and email. All these payload parameters are necessary. Ensure you put in a valid email. 

### Fetching all Users
Endpoint: `/users`
Method: `GET`

### Login

#### Google Login
Endpoint :`/authorize/google`
Method: `GET`

Instructions: 
This endpoint generates an authorization url. This authorization url is then clicked by the user which redirects it into a google sign in page. 
After sigin it, it redirects back to our callback function which in turn generates a jwt access_token and refresh_token. 


#### Normal Login
Endpoint: `/token`
Method: `/POST`
Content-Type: `form/data`
Payload: username and password.

Response: Generates an access and refresh token. 

#### Refresh access tokens
Endpoint: `/refresh?refresh_token=your_refresh_token`
Method: `POST`
query_paremeter: refresh_token

Response: Generates a new access_token


### Booking Endpoints

#### Create a booking
Endpoint: `/bookings`
Method: `/POST`
Authorization(Header): "Bearer {access_token}". Pass your access token as a header
payload:
      - booking_time: ISO format datetime of the start period you want to book for
      - end_time: ISO format datetime of the endpoint period you want to book for. Optional if the is_recurring is set to None
      - is_recurring: to specify if the booking is recurring. Either True or False.
      - description: Description of the booking you want
      - recurrence_interval: In the case `is_recurring` is set to True, then the recurrence_interval has to be set. Whether it is daily, weekly or monthly. 
      - is_cancelled: Specifies if the booking has been cancelled.


NB: End_time can't be lesser than booking time. 

#### Fetching user bookies
Endpoint: `/bookings/`
Method: `GET`
Authorization(Header): "Bearer {access_token}". Pass your access token as a header

Response:

Returns all the bookings associated with user


#### Updating a booking
Endpoint: `/bookings/{booking_id}`
Method: `PUT`
Path Parameter: booking_id - specifies the id of the booking you want update. 
payload: whatever field you want updated. However keep in mind that there are some constraints. Can't change booking time to be lower than the current time or greater than end_time.
Authorization(Header): "Bearer {access_token}". Pass your access token as a header

#### Cancelling a booking

Endpoint: `/bookings/{booking_id}`
Method: `DELETE`,
Path Parameter: booking_id - id used
Authorization(Header): "Bearer {access_token}". Pass your access token as a header

#### Booking history

Endpoint: `bookings/history`
Method: `GET`
Authorization(Header): "Bearer {access_token}". Pass your access token as a header

Response: Returns all the past bookings

#### Upcoming Bookings
Endpoint: `bookings/upcoming`
Method: `GET`
Authorization(Header): "Bearer {access_token}". Pass your access token as a header

Response: Returns all the upcoming bookings
