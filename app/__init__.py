from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_moment import Moment
from flask_cors import CORS
from .models import db, ma, User, Dog, Org
from .api.__init__ import api
from .auth.__init import auth
from helpers import JSONEncoder

app = Flask(__name__)

CORS(app, resources={r"/auth/*": {
    "origins": "*",
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["OPTIONS", "POST", "GET", "DELETE", "PUT"]
}})

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(auth, url_prefix='/auth')

app.json_encoder = JSONEncoder
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db, compare_type=True)
ma.init_app(app)
moment = Moment(app)
jwt = JWTManager(app)
