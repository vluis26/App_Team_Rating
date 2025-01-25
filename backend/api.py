from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from flask_cors import CORS
from datetime import datetime, timezone
import logging

from ticketmaster_service import search_events

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
api = Api(app)

# associate ratings with specific users
class UserModel(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)

    ratings = db.relationship('RestaurantRatingModel', backref='user', lazy=True)

    def __repr__(self): 
        return f"User(name = {self.name}, email = {self.email})"

# Details of each restaurant visit
class RestaurantRatingModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_name = db.Column(db.String(100), nullable=False)
    restaurant_type = db.Column(db.String(120), nullable=False)
    restaurant_address = db.Column(db.String(150), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    meal = db.Column(db.String, nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    
    # Associate with the user
    user_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=True)
    
    # Dynamic attribute for events
    _events = None

    def __repr__(self):
        return f"RestaurantRating(restaurant_name={self.restaurant_name}, rating={self.rating})"
    
    @property
    def events(self):
        """Dynamic property to hold events data."""
        return self._events if self._events else []
    
    @events.setter
    def events(self, value):
        """Setter for the dynamic events property."""
        self._events = value


# Request Parsers
rating_args = reqparse.RequestParser()
rating_args.add_argument('restaurant_name', type=str, required=True, help="Restaurant name cannot be blank")
rating_args.add_argument('restaurant_type', type=str, required=True, help="Restaurant type cannot be blank")
rating_args.add_argument('restaurant_address', type=str, required=True, help="Restaurant address cannot be blank")
rating_args.add_argument('rating', type=int, required=True, choices=[1,2,3,4,5], help="Rating (1-5) is required")
rating_args.add_argument('meal', type=str, required=True, help="Meal cannot be empty")
# rating_args.add_argument('photo', type=str, required=False)
rating_args.add_argument('calories', type=int, required=True, help="Calories cannot be empty")
# We want  date_posted to be blank to prevent client manipulation
# rating_args.add_argument('date_posted', type=, required=True, help="Time cannot be blank")
rating_args.add_argument('user_id', type=int, required=False)


# Output Fields
event_fields = {
    'id': fields.String(attribute='id'),
    'name': fields.String(attribute='name'),
    'url': fields.String(attribute='url'),
}

rating_fields = {
    'id': fields.Integer,
    'restaurant_name': fields.String,
    'restaurant_type': fields.String,
    'restaurant_address': fields.String,
    'rating': fields.Integer,
    'meal': fields.String,
    'calories': fields.Integer,
    'user_id': fields.Integer,
    'date_posted': fields.DateTime(dt_format='iso8601'),
    'events': fields.List(fields.Nested(event_fields)),  # New field for events
}

def extract_city(address):
    try:
        # Split the address by commas
        parts = address.split(',')
        # Assuming the city is the second part
        city = parts[1].strip()
        return city
    except IndexError:
        return None


# API Resources
class RestaurantRatings(Resource):
    @marshal_with(rating_fields)
    def post(self):
        '''
        Add a new restaurant rating and fetch nearby events.
        '''
        args = rating_args.parse_args()
        address = args['restaurant_address']
        
        # Extract city from address
        city = extract_city(address)
        
        if not city:
            abort(400, message="Could not extract city from address.")
        
        # Create new RestaurantRating instance
        new_rating = RestaurantRatingModel(
            restaurant_name=args['restaurant_name'],
            restaurant_type=args['restaurant_type'],
            restaurant_address=address,
            rating=args['rating'],
            meal=args['meal'],
            calories=args['calories'],
            user_id=args.get('user_id'),
            city=city
        )
        
        db.session.add(new_rating)
        db.session.commit()
        
        # Fetch events from Ticketmaster API
        try:
            events = search_events(city=city, max_events=3, classificationName='Music')  # Adjust classification as needed
            logging.debug(f"Fetched Events: {events}")
        except Exception as e:
            logging.error(f"Error fetching events: {e}")
            events = []  # Handle API call failures gracefully
        
        # Assign events to the dynamic property
        new_rating.events = events
        
        # Serialize the response using Marshmallow
        return new_rating, 201
    
    @marshal_with(rating_fields)
    def get(self):
        """
        Retrieve all restaurant ratings with optional filtering.
        Supports filters:
            - restaurant_type
            - min_rating
            - max_rating
        """
        parser = reqparse.RequestParser()
        parser.add_argument('restaurant_type', type=str, location='args')
        parser.add_argument('min_rating', type=int, location='args')
        parser.add_argument('max_rating', type=int, location='args')
        args = parser.parse_args()

        query = RestaurantRatingModel.query

        if args['restaurant_type']:
            query = query.filter(RestaurantRatingModel.restaurant_type.ilike(f"%{args['restaurant_type']}%"))
        if args['min_rating']:
            query = query.filter(RestaurantRatingModel.rating >= args['min_rating'])
        if args['max_rating']:
            query = query.filter(RestaurantRatingModel.rating <= args['max_rating'])

        ratings = query.all()

        # Assign events to each rating
        for rating in ratings:
            try:
                events = search_events(city=rating.city, max_events=3, classificationName='Music')
                rating.events = events
            except Exception as e:
                logging.error(f"Error fetching events for rating ID {rating.id}: {e}")
                rating.events = []
        
        return ratings, 200

class RestaurantRating(Resource):
    @marshal_with(rating_fields)
    def get(self, id):
        '''
        Retrieve restaurant rating by ID along with related events.
        '''
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')
        
        # Fetch events from Ticketmaster API
        try:
            events = search_events(city=rating.city, max_events=3, classificationName='Music')
            logging.debug(f"Fetched Events for rating ID {id}: {events}")
        except Exception as e:
            logging.error(f"Error fetching events for rating ID {id}: {e}")
            events = []  # Handle API call failures gracefully
        
        # Assign events to the dynamic property
        rating.events = events
        
        return rating, 200
    
    @marshal_with(rating_fields)
    def patch(self, id):
        '''
        Update fields of a restaurant rating.
        '''
        args = rating_args.parse_args()
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')

        # update fields
        rating.restaurant_name = args.get('restaurant_name', rating.restaurant_name)
        rating.restaurant_type = args.get('restaurant_type', rating.restaurant_type)
        rating.restaurant_address = args.get('restaurant_address', rating.restaurant_address)
        rating.rating = args.get('rating', rating.rating)
        rating.meal = args.get('meal', rating.meal)
        # rating.photo = args.get('photo', rating.photo)  # Uncomment if handling photos
        rating.calories = args.get('calories', rating.calories)
        rating.user_id = args.get('user_id', rating.user_id)

        db.session.commit()
        return rating, 200
    
    @marshal_with(rating_fields)
    def delete(self, id):
        '''
        Delete a restaurant rating by ID
        '''
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')
        db.session.delete(rating)
        db.session.commit()
        return {'message': 'Deleted'}, 200

class AggregatedData(Resource):
    def get(self):
        """
        Retrieve aggregated data: average ratings.
        """
        from sqlalchemy import func

        aggregation = db.session.query(
            RestaurantRatingModel.restaurant_name,
            func.avg(RestaurantRatingModel.rating).label('average_rating'),
        ).group_by(RestaurantRatingModel.restaurant_name).all()

        result = []
        for agg in aggregation:
            result.append({
                'restaurant_name': agg.restaurant_name,
                'average_rating': round(agg.average_rating, 2) if agg.average_rating else None,
            })
        return result, 200



# Resources to API
api.add_resource(RestaurantRatings, '/api/ratings/')
api.add_resource(RestaurantRating, '/api/ratings/<int:id>')
api.add_resource(AggregatedData, '/api/ratings/aggregated/')


if __name__ == '__main__':
    app.run(debug=True) 