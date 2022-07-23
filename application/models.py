from sqlalchemy import ForeignKey
from .database import db

class Logs(db.Model):
    __tablename__ = 'Logs'
    LogID = db.Column(db.Integer, autoincrement= True, primary_key=True)
    UserName = db.Column(db.String, nullable=False)
    Tracker_name = db.Column(db.String, nullable=False)
    Date_created = db.Column(db.String, nullable=False)
    Last_modified = db.Column(db.String, nullable=False)
    Value = db.Column(db.String, nullable = False)
    Description = db.Column(db.String, nullable = True)

class Trackers(db.Model):
    __tablename__ = 'Trackers'
    UserName = db.Column(db.String, nullable=False, primary_key=True)
    Tracker_name = db.Column(db.String, nullable=False, primary_key=True)
    Description = db.Column(db.String)

class User(db.Model):
    __tablename__ = 'User'
    UserName = db.Column(db.String, nullable=False, unique=True, primary_key=True)
    Password = db.Column(db.String, nullable=False)