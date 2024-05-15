from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment
from flask_cors import CORS
from .models import db, ma, login_manager, User
from .api import api
from .auth import auth
from helpers import JSONEncoder


app = Flask(__name__)

CORS(app, resources={r"/api/*": {
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
login_manager.init_app(app)
ma.init_app(app)
moment = Moment(app)


#If issues logging in this may be the cause.  This is the function that will load the user from the database.  It will be called when the user logs in and is authenticated.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# with the @login_required decorator, this will redirect to the login page if the user is not logged in.  Keeps users from accessing pages they shouldn't be able to access by typing in the address manually.
login_manager.login_view = 'login'
