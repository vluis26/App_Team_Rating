from flask_restful import Resource, reqparse, marshal_with, abort, fields
from sqlalchemy import func
from app.models import RestaurantRatingModel
from app.utils.helpers import extract_city, fetch_and_assign_events
from app.extensions import db
import logging

# Request Parsers
rating_args = reqparse.RequestParser()
rating_args.add_argument('restaurant_name', type=str, required=True, help="Restaurant name cannot be blank")
rating_args.add_argument('restaurant_type', type=str, required=True, help="Restaurant type cannot be blank")
rating_args.add_argument('restaurant_address', type=str, required=True, help="Restaurant address cannot be blank")
rating_args.add_argument('rating', type=int, required=True, choices=[1,2,3,4,5], help="Rating (1-5) is required")
rating_args.add_argument('meal', type=str, required=True, help="Meal cannot be empty")
rating_args.add_argument('calories', type=int, required=True, help="Calories cannot be empty")
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
    'events': fields.List(fields.Nested(event_fields)),
}

class RestaurantRatings(Resource):
    """
    Resource for handling multiple restaurant ratings.
    - POST: Add a new restaurant rating and fetch nearby events.
    - GET: Retrieve a list of restaurant ratings with optional filters.
    """
    @marshal_with(rating_fields)
    def post(self):
        '''
        Add a new restaurant rating and fetch nearby events.

        Returns:
            dict: A dictionary containing the restaurant rating and nearby events.
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
        
        # Fetch and assign events using the helper function
        fetch_and_assign_events(new_rating)
        
        return new_rating, 201

    @marshal_with(rating_fields)
    def get(self):
        """
        Retrieve all restaurant ratings with optional filtering.
        Supports filters:
            - restaurant_type
            - min_rating
            - max_rating

        Returns:
            list: A list of restaurant ratings with optional filters applied. 
        """
        parser = reqparse.RequestParser()
        parser.add_argument('restaurant_name', type=str, location='args')
        parser.add_argument('restaurant_type', type=str, location='args')
        parser.add_argument('min_rating', type=int, location='args')
        parser.add_argument('max_rating', type=int, location='args')
        args = parser.parse_args()

        query = RestaurantRatingModel.query

        # Types of filters that can be applied
        if args['restaurant_name']:
            query = query.filter(RestaurantRatingModel.restaurant_name.ilike(f"%{args['restaurant_name']}%"))
        if args['restaurant_type']:
            query = query.filter(RestaurantRatingModel.restaurant_type.ilike(f"%{args['restaurant_type']}%"))
        if args['min_rating']:
            query = query.filter(RestaurantRatingModel.rating >= args['min_rating'])
        if args['max_rating']:
            query = query.filter(RestaurantRatingModel.rating <= args['max_rating'])

        ratings = query.all()

        # Assign events to each rating using the helper function
        for rating in ratings:
            fetch_and_assign_events(rating)
        
        return ratings, 200

class RestaurantRating(Resource):
    """
    Resource for handling a single restaurant rating.
    - GET: Retrieve a specific restaurant rating by ID along with related events.
    - PATCH: Update fields of a specific restaurant rating.
    - DELETE: Delete a specific restaurant rating by ID.
    """
    @marshal_with(rating_fields)
    def get(self, id):
        '''
        Retrieve restaurant rating by ID along with related events.

        Args:
            id (int): The ID of the restaurant rating.

        Returns:
            dict: A dictionary containing the restaurant rating and related events.
        '''
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')
        
        # Fetch and assign events using the helper function
        fetch_and_assign_events(rating)
        
        return rating, 200
    
    @marshal_with(rating_fields)
    def patch(self, id):
        '''
        Update fields of a restaurant rating.

        Args:
            id (int): The ID of the restaurant rating.

        Returns:
            dict: A dictionary containing the updated restaurant rating.
        '''
        args = rating_args.parse_args()
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')

        # Update fields
        rating.restaurant_name = args.get('restaurant_name', rating.restaurant_name)
        rating.restaurant_type = args.get('restaurant_type', rating.restaurant_type)
        rating.restaurant_address = args.get('restaurant_address', rating.restaurant_address)
        rating.rating = args.get('rating', rating.rating)
        rating.meal = args.get('meal', rating.meal)
        # rating.photo = args.get('photo', rating.photo)  # Uncomment if handling photos
        rating.calories = args.get('calories', rating.calories)

        # Re-extract city if address has changed
        if 'restaurant_address' in args and args['restaurant_address'] != rating.restaurant_address:
            new_city = extract_city(rating.restaurant_address)
            if new_city:
                rating.city = new_city
                # Fetch and assign events using the helper function
                fetch_and_assign_events(rating)
            else:
                abort(400, message="Could not extract city from new address.")

        db.session.commit()
        return rating, 200
    
    @marshal_with(rating_fields)
    def delete(self, id):
        '''
        Delete a restaurant rating by ID

        Args:
            id (int): The ID of the restaurant rating.

        Returns:
            dict: A dictionary containing a message indicating the deletion status.
        '''
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')
        db.session.delete(rating)
        db.session.commit()
        return {'message': 'Deleted'}, 200

class Average_Ratings(Resource):
    """
    Resource for handling aggregated restaurant rating data.
    - GET: Retrieve aggregated data such as average ratings per restaurant.
    """
    def get(self):
        """
        Retrieve aggregated data: average ratings per restaurant.
        
        Returns:
            list: A list of dictionaries containing restaurant names and their average ratings.
        """
        try:
            # Query to calculate average rating per restaurant
            aggregation = db.session.query(
                RestaurantRatingModel.restaurant_name,
                func.avg(RestaurantRatingModel.rating).label('average_rating')
            ).group_by(RestaurantRatingModel.restaurant_name).all()

            # Format the results
            result = []
            for agg in aggregation:
                result.append({
                    'restaurant_name': agg.restaurant_name,
                    'average_rating': round(agg.average_rating, 2) if agg.average_rating else None,
                })

            return result, 200
        except Exception as e:
            logging.error(f"Error retrieving aggregated data: {e}")
            abort(500, message="Internal server error while retrieving aggregated data.")