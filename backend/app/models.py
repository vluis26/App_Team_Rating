from app.extensions import db
from datetime import datetime, timezone

class UserModel(db.Model): 
    __tablename__ = 'user_model'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)

    ratings = db.relationship('RestaurantRatingModel', backref='user', lazy=True)

    def __repr__(self): 
        return f"User(name={self.name}, email={self.email})"

class RestaurantRatingModel(db.Model):
    __tablename__ = 'restaurant_rating_model'
    
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
