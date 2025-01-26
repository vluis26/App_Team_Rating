# Initializes all Flask extensions, without binding them to the Flask app instance.

from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api

db = SQLAlchemy()
api = Api()