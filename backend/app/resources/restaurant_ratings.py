from flask_restful import Resource, reqparse, marshal_with, abort, fields
from sqlalchemy import func
from app.models import RestaurantRatingModel, UserModel
from app.utils.helpers import extract_city, fetch_and_assign_events
from app.extensions import db
import logging

# POST Parser
rating_post_args = reqparse.RequestParser()
rating_post_args.add_argument('restaurant_name', type=str, required=True, help="Restaurant name cannot be blank")
rating_post_args.add_argument('restaurant_type', type=str, required=True, help="Restaurant type cannot be blank")
rating_post_args.add_argument('restaurant_address', type=str, required=True, help="Restaurant address cannot be blank")
rating_post_args.add_argument('rating', type=int, required=True, choices=[1,2,3,4,5], help="Rating (1-5) is required")
rating_post_args.add_argument('meal', type=str, required=True, help="Meal cannot be empty")
rating_post_args.add_argument('calories', type=int, required=True, help="Calories cannot be empty")
rating_post_args.add_argument('user_id', type=int, required=False, help="ID of the user submitting the rating")
rating_post_args.add_argument('name', type=str, required=False, help="Name of the user (required if user_id is not provided)")
rating_post_args.add_argument('email', type=str, required=False, help="Email of the user (required if user_id is not provided)")

# PATCH Parser
rating_patch_args = reqparse.RequestParser()
rating_patch_args.add_argument('restaurant_name', type=str, required=False)
rating_patch_args.add_argument('restaurant_type', type=str, required=False)
rating_patch_args.add_argument('restaurant_address', type=str, required=False)
rating_patch_args.add_argument('rating', type=int, required=False, choices=[1,2,3,4,5], help="Rating (1-5) is required")
rating_patch_args.add_argument('meal', type=str, required=False)
rating_patch_args.add_argument('calories', type=int, required=False)

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

average_rating_fields = {
    'restaurant_name': fields.String,
    'average_rating': fields.Float
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
        args = rating_post_args.parse_args()
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
        args = rating_patch_args.parse_args()  # Use the PATCH parser
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')

        # Update fields only if they are provided
        if args['restaurant_name']:
            rating.restaurant_name = args['restaurant_name']
        if args['restaurant_type']:
            rating.restaurant_type = args['restaurant_type']
        if args['restaurant_address']:
            rating.restaurant_address = args['restaurant_address']
            # Re-extract city if address has changed
            new_city = extract_city(rating.restaurant_address)
            if new_city:
                rating.city = new_city
            else:
                abort(400, message="Could not extract city from new address.")
        if args['rating']:
            rating.rating = args['rating']
        if args['meal']:
            rating.meal = args['meal']
        if args['calories']:
            rating.calories = args['calories']
        if args['user_id']:
            # Associate with an existing user
            user = UserModel.query.get(args['user_id'])
            if not user:
                abort(400, message=f"User with id '{args['user_id']}' does not exist.")
            rating.user_id = args['user_id']

        db.session.commit()

        # Fetch and assign events using the helper function
        fetch_and_assign_events(rating)

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

class Average_Rating(Resource):
    """
    Resource for retrieving the average rating of a specific restaurant.
    - GET: Retrieve the average rating for the given restaurant_name.
    """
    @marshal_with(average_rating_fields)
    def get(self, restaurant_name):
        """
        Retrieve the average rating for a specific restaurant.

        Args:
            restaurant_name (str): The name of the restaurant.

        Returns:
            dict: A dictionary containing the restaurant name and its average rating.
        """
        try:
            # Query to calculate average rating for the specified restaurant_name
            aggregation = db.session.query(
                RestaurantRatingModel.restaurant_name,
                func.avg(RestaurantRatingModel.rating).label('average_rating')
            ).filter(
                RestaurantRatingModel.restaurant_name.ilike(f"%{restaurant_name}%")
            ).group_by(
                RestaurantRatingModel.restaurant_name
            ).first()

            if not aggregation:
                abort(404, message=f"No ratings found for restaurant '{restaurant_name}'.")

            # Round the average rating to two decimal places
            average_rating = round(aggregation.average_rating, 2) if aggregation.average_rating else None

            return {
                'restaurant_name': aggregation.restaurant_name,
                'average_rating': average_rating
            }, 200

        except Exception as e:
            logging.error(f"Error retrieving average rating for '{restaurant_name}': {e}")
            abort(500, message="Internal server error while retrieving average rating.")

class UserRatings(Resource):
    """
    Resource for retrieving all restaurant ratings submitted by a specific user.
    - GET: Retrieve all ratings posted by the given user_id.
    """
    @marshal_with(rating_fields)
    def get(self, user_id):
        """
        Retrieve all restaurant ratings submitted by a specific user.
        
        Args:
            user_id (int): The ID of the user.
        
        Returns:
            list: A list of restaurant ratings submitted by the user.
        """
        # Check if the user exists
        user = UserModel.query.filter_by(id=user_id).first()
        if not user:
            abort(404, message=f"User with id '{user_id}' not found.")
        
        # Retrieve all ratings submitted by the user
        user_ratings = RestaurantRatingModel.query.filter_by(user_id=user_id).all()
        
        if not user_ratings:
            abort(404, message=f"No ratings found for user with id '{user_id}'.")
        
        # Assign events to each rating using the helper function
        for rating in user_ratings:
            fetch_and_assign_events(rating)
        
        return user_ratings, 200
