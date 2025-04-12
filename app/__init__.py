from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///video_processor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # Add a secret key for sessions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

from app import routes, models

# Create database tables
with app.app_context():
    db.create_all()