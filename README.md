# App_Team_Rating
The Restaurant Rating API is RESTful service designed to allow users to submit, retrieve, update, and delete restaurant ratings. It provides aggregated data such as average ratings per restaurant and allows users to view all ratings (filter: restaurant_name, restaurant_type, min/max rating, and by specific user). The API integrates a third-party API, TicketMaster API, to fetch events bases on the restaurant's location.

# Big-Picture Design Decisions
## Modular and Scalable Design
- The API is designed with a modular structure, easy to maintain and scale
- ![Screenshot 2025-01-27 at 12 58 06 AM](https://github.com/user-attachments/assets/1cf1eea6-1423-4a0b-ae03-f0b939301ec5)

## RESTful API Principles
- HTTP methods map directly to CRUD operations

## Data Validation and Error Handling
- Input validation is implemented using reqparse to ensure data integrity.

## Integration with a Third-Party API
- The integration with the TicketMaster API adds value by fetching relevant events based on restaurant locations.

## Filtering and Aggregation
- Filtering options (e.g., by restaurant name, type, or rating range) are included to allow clients to retrieve specific subsets of data.

## Flexibility in Data Model
- The RestaurantRatingModel includes fields like restaurant_type, meal, calories, and city to ensure flexibility for various types of data.
- Dynamic fields like events are designed to hold third-party API data without altering the database schema.

# Database

- SQLite: A lightweight, file-based database used for development and testing purposes. Easily replaceable with more robust databases like PostgreSQL for production environments.


# Choice of Tools

- Flask: A lightweight WSGI web application framework used for building the API.
- Flask-RESTful: An extension for Flask that adds support for quickly building REST APIs.
- SQLAlchemy: A powerful ORM (Object-Relational Mapping) library for managing database interactions.


# Setup

### Clone the Repository
```bash
git clone https://github.com/yourusername/restaurant-rating-api.git
cd restaurant-rating-api/backend
```
### Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```
### Install dependencies
```bash
pip install -r requirements.txt
```
### Initialize the Database
```bash
mkdir -p instance
python create_db.py
```
### Create a User
```bash
start Flask Shell
flask shell
from app.extensions import db

# Create a new user with id=1
new_user = UserModel(id=1, name="John Doe", email="john.doe@example.com")
db.session.add(new_user)
db.session.commit()

# Verify creation
user = UserModel.query.get(1)
print(user)
exit()
```
### Running the API
```bash
source venv/bin/activate
python run.py
```

# API Endpoints
## 1. /api/ratings/, method: POST
### Example Request body: Adds a new restaurant rating and fetches related events:
```bash
{
    "restaurant_name": "Hibachi and Co",
    "restaurant_type": "Chinese",
    "restaurant_address": "1234 Chicken Street, Raleigh, NC",
    "rating": 4,
    "meal": "Peking Duck",
    "calories": 800,
    "user_id": 1
}
```
## 2. /api/ratings/, method: GET
### Example Request: Retrieves a list of all restaurant ratings with optional filtering:
```bash
curl "http://localhost:5000/api/ratings/?restaurant_type=Chinese&min_rating=3"
```
## 3. /api/ratings/<int:id>, method: GET
### Example Request: Retrieves a specific restaurant rating by its unique ID:
```bash
curl http://localhost:5000/api/ratings/1
```
## 4. /api/ratings/<int:id>, method: PATCH
### Example Request body: Partially updates fields of a specific restaurant rating:
```bash
{
    "rating": 5,
    "meal": "Kung Pao Chicken"
}
```
## 5. /api/ratings/<int:id>, method: DELETE
### Example Request: Deletes a specific restaurant rating by its unique ID:
```bash
curl -X DELETE http://localhost:5000/api/ratings/1
```
## 6. /api/ratings/average_ratings/, method: GET
### Example Request: Retrieves aggregated data, specifically the average ratings for each restaurant.
```bash
curl http://localhost:5000/api/ratings/average_ratings/
```
## 7. /api/ratings/average_ratings/<string:restaurant_name>, method: GET
### Example Request: Retrieves the average rating for a specified restaurant:
```bash
curl http://localhost:5000/api/ratings/average_ratings/Chinatown%20Delight
```
## 8. /api/users/<int:user_id>/ratings, method: GET
### Example Request: Retrieves all restaurant ratings submitted by a specific use:
```bash
curl http://localhost:5000/api/users/1/ratings
```
