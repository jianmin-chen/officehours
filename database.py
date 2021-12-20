from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Set up database
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String, nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    avatar = db.Column(db.String, nullable=False, unique=True)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String, nullable=False)
    token = db.Column(db.String)

    in_charge = db.relationship("Group", back_populates="creator")
    part_of = db.relationship("Member", back_populates="user")
    messages = db.relationship("Message", back_populates="user")

class Group(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    creator = db.relationship("User", back_populates="in_charge")
    members = db.relationship("Member", back_populates="group")
    messages = db.relationship("Message", back_populates="group")


class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    group = db.relationship("Group", back_populates="members")
    user = db.relationship("User", back_populates="part_of")

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    public = db.Column(db.Boolean, default=False, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    group = db.relationship("Group", back_populates="messages")
    user = db.relationship("User", back_populates="messages")
