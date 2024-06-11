from flask import Flask, request, make_response
from .api.config import Config
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_moment import Moment
from flask_cors import CORS
from .models import User, Dog, Org, fav_dog, db, ma
from helpers import JSONEncoder
from dotenv import load_dotenv
from .api.__init__ import api
from .auth.__init__ import auth
import os

def create_app():
    load_dotenv()

    app = Flask(__name__)

    app.config.from_object(Config)

    CORS(app)

    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth, url_prefix='/auth')

    app.json_encoder = JSONEncoder

    db.init_app(app)
    migrate = Migrate(app, db)
    moment = Moment(app)
    ma.init_app(app)

    with app.app_context():
        db.create_all()
        from app.auth.scheduler import start_scheduler
        start_scheduler(app)

    return app

app = create_app()