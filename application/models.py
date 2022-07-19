from sqlalchemy import ForeignKey
from .database import db

class Logs(db.Model):
    __tablename__ = 'Logs'
    UserName = db.Column(db.String, nullable=False)
    LogID = db.Column(db.Integer, autoincrement= True, primary_key=True)
    Last_modified = db.Column(db.String, nullable=False)
    Value = db.Column(db.String, nullable = False)
    Description = db.Column(db.String, nullable = True)

class User(db.Model):
    __tablename__ = 'User'
    UserName = db.Column(db.String, nullable=False, unique=True, primary_key=True)
    Password = db.Column(db.String, nullable=False)