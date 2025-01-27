# App_Team_Rating
The Restaurant Rating API is RESTful service designed to allow users to submit, retrieve, update, and delete restaurant ratings. It provides aggregated data such as average ratings per restaurant and allows users to view all ratings (filter: restaurant_name, restaurant_type, min/max rating, and by specific user). The API integrates a third-party API, TicketMaster API, to fetch events bases on the restaurant's location.

### 1. **Choice of Tools**

- **Flask:** A lightweight WSGI web application framework used for building the API.
- **Flask-RESTful:** An extension for Flask that adds support for quickly building REST APIs.
- **SQLAlchemy:** A powerful ORM (Object-Relational Mapping) library for managing database interactions.


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
## 7. /api/ratings/average_rating/<string:restaurant_name>, method: GET
### Example Request: Retrieves the average rating for a specified restaurant:
```bash
curl http://localhost:5000/api/ratings/average_rating/Chinatown%20Delight
```
## 8. /api/users/<int:user_id>/ratings, method: GET
### Example Request: Retrieves all restaurant ratings submitted by a specific use:
```bash
curl http://localhost:5000/api/users/1/ratings
```
