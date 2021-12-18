from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Set up database
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, unique=True)
    google_account = db.Column(db.Boolean, default=False, nullable=False)

    def __str__(self):
        """Return string version of user."""
        return f"User #{self.id}: {self.name}"
