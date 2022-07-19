import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from application.database import db

current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(current_dir, 'database.sqlite3')
db = SQLAlchemy()
db.init_app(app)
api = Api(app)
app.app_context().push()

from application.controllers import *

if __name__ == "__main__":
    app.run(debug = True)
