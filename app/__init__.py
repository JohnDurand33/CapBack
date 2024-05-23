from flask import Flask
from .api.config import Config
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_moment import Moment
from flask_cors import CORS
from .models import User, Dog, Org, fav_dog, db, ma
from helpers import JSONEncoder
from .scheduler import scheduler, start_scheduler
from dotenv import load_dotenv
from .api.__init__ import api
from .auth.__init import auth
import os


def create_app():
    load_dotenv()

    app = Flask(__name__)

    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    print(f'db_uri: {db_uri}')
    if not db_uri:
        raise RuntimeError(
            "SQLALCHEMY_DATABASE_URI environment variable not set")
    print(f"SQLALCHEMY_DATABASE_URI from environment: {
          db_uri}")  # Debug print statement

    app.config.from_object(Config)  # Load config from Config class

    # Check if the config has been set correctly
    sqlalchemy_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    print(f'sqlalchemy_uri: {sqlalchemy_uri}')
    if not sqlalchemy_uri:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI not set in app.config")
    print(f"SQLALCHEMY_DATABASE_URI in create_app: {
          sqlalchemy_uri}")  # Debug print statement

    CORS(app, resources={r"/auth/*": {
        "origins": "*",
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["OPTIONS", "POST", "GET", "DELETE", "PUT"]
    }})

    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth, url_prefix='/auth')

    app.json_encoder = JSONEncoder

    db.init_app(app)
    migrate = Migrate(app, db)
    moment = Moment(app)
    ma.init_app(app)

    with app.app_context():
        db.create_all()
        start_scheduler(app)  # Start the scheduler with the app context

    return app


app = create_app()
