from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from app.extensions import db, api
from app.resources.restaurant_ratings import RestaurantRatings, RestaurantRating, Average_Ratings, Average_Rating, UserRatings

# Initialize logging early to capture all logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# Register resources
api.add_resource(RestaurantRatings, '/api/ratings/')
api.add_resource(RestaurantRating, '/api/ratings/<int:id>')
api.add_resource(Average_Ratings, '/api/ratings/average_ratings/')
api.add_resource(Average_Rating, '/api/ratings/average_ratings/<string:restaurant_name>')
api.add_resource(UserRatings, '/api/users/<int:user_id>/ratings')



def create_app():
    app = Flask(__name__)
    CORS(app)

    # Load environment variables
    load_dotenv()

    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with app
    db.init_app(app)
    api.init_app(app)

    # Diagnostic: Print all registered routes
    logging.debug("Registered Routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        logging.debug(f"{rule} -> {rule.endpoint} [{methods}]")

    return app
