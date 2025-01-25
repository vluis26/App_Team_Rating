from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from flask_cors import CORS
from datetime import datetime

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
    # photo = db.Column(nullable=True)
    calories = db.Column(db.Integer, nullable=False)
    # time/date
    # date_posted = db.Column()

    # associate with the user
    user_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=True)
    
    def __repr__(self):
        return f"RestaurantRating(restaurant_name={self.restaurant_name}, rating={self.rating})"

# Request Parsers
rating_args = reqparse.RequestParser()
rating_args.add_argument('restaurant_name', type=str, required=True, help="Restaurant name cannot be blank")
rating_args.add_argument('restaurant_type', type=str, required=True, help="Restaurant type cannot be blank")
rating_args.add_argument('restaurant_address', type=str, required=True, help="Restaurant address cannot be blank")
rating_args.add_argument('rating', type=int, required=True, help="Rating (1-5) is required")
rating_args.add_argument('meal', type=str, required=True, help="Meal cannot be empty")
# rating_args.add_argument('photo', type=str, required=False)
rating_args.add_argument('calories', type=int, required=True, help="Calories cannot be empty")
# rating_args.add_argument('meal_datetime', type=, required=True, help="Time cannot be blank")
rating_args.add_argument('user_id', type=int, required=False)


# Output Fields
rating_fields = {
    'id': fields.Integer,
    'restaurant_name': fields.String,
    'restaurant_type': fields.String,
    'rating': fields.Integer,
    # 'meal_datetime': fields.DateTime(),
    'meal': fields.String,
    # 'photo': fields.String
    'calories': fields.Integer,
    'user_id': fields.Integer,
}

# API Resources
class RestaurantRatings(Resource):
    @marshal_with(rating_fields)
    def post(self):
        '''
        Add a new restaurant rating.
        '''
        args = rating_args.parse_args()
        new_rating = RestaurantRatingModel(
            restaurant_name=args['restaurant_name'],
            restaurant_type=args['restaurant_type'],
            restaurant_address=args['restaurant_address'],
            rating=args['rating'],
            meal=args['meal'],
            # photo=args.get('photo'),  # Uncomment if handling photos
            calories=args['calories'],
            # meal_datetime=args.get('meal_datetime', datetime.utcnow()),  # Uncomment if needed
            user_id=args.get('user_id')
        )
        db.session.add(new_rating)
        db.session.commit()
        return new_rating, 200

class RestaurantRating(Resource):
    @marshal_with(rating_fields)
    def get(self, id):
        '''
        Retrieve restaurant rating ID,
        '''
        rating = RestaurantRatingModel.query.filter_by(id=id).first()
        if not rating:
            abort(404, message='Restaurant rating not found.')
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
        # rating.meal_datetime = args.get('meal_datetime', rating.meal_datetime)  # Uncomment if needed
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


# Resources to API
api.add_resource(RestaurantRatings, '/api/ratings/')
api.add_resource(RestaurantRating, '/api/ratings/<int:id>')


@app.route('/')
def home():
    return '<h1>Flask REST API</h1>'

if __name__ == '__main__':
    app.run(debug=True) 