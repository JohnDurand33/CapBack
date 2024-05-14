from secrets import token_hex
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_marshmallow import Marshmallow
from flask_login import UserMixin
from flask_login import LoginManager

login_manager = LoginManager()
ma = Marshmallow()
db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    user_created = db.Column(db.DateTime,       nullable=False,
                             default=lambda: datetime.now(timezone.utc))
    
    token = db.Column(db.String, default='', unique=True)
    token_expiry = db.Column(db.DateTime, nullable=False,
                             default=lambda: datetime.now(timezone.utc))
    breed_1 = db.Column(db.String(100), nullable=False)
    breed_1_img = db.Column(db.String(200), nullable=False)
    breed_2 = db.Column(db.String(100), nullable=False)
    breed_2_img = db.Column(db.String(200), nullable=False)
    breed_3 = db.Column(db.String(100), nullable=False)
    breed_3_img = db.Column(db.String(200), nullable=False)
    breed_4 = db.Column(db.String(100), nullable=False)
    breed_4_img = db.Column(db.String(200), nullable=False)
    breed_5 = db.Column(db.String(100), nullable=False)
    breed_5_img = db.Column(db.String(200), nullable=False)
    breed_6 = db.Column(db.String(100), nullable=False)
    breed_6_img = db.Column(db.String(200), nullable=False)
    breed_7 = db.Column(db.String(100), nullable=False)
    breed_7_img = db.Column(db.String(200), nullable=False)
    breed_8 = db.Column(db.String(100), nullable=False)
    breed_8_img = db.Column(db.String(200), nullable=False)
    breed_9 = db.Column(db.String(100), nullable=False)
    breed_9_img = db.Column(db.String(200), nullable=False)
    breed_10 = db.Column(db.String(100), nullable=False)
    breed_10_img = db.Column(db.String(200), nullable=False)
    dogs = db.relationship('Dog', backref='user', lazy=True)
    

    def __init__(self, f_name, username, email, password, zip_code):
        self.f_name = f_name
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.zip_code = zip_code
        self.token = token_hex(16)

    class UserSchema(ma.Schema):
        class Meta:
            fields = ('id', 'f_name', 'username', 'email', 'password', 'zip_code', 'user_created', 'token', 'token_expiry', 'breed_1', 'breed_1_img', 'breed_2', 'breed_2_img', 'breed_3', 'breed_3_img', 'breed_4', 'breed_4_img', 'breed_5', 'breed_5_img', 'breed_6', 'breed_6_img', 'breed_7', 'breed_7_img', 'breed_8', 'breed_8_img', 'breed_9', 'breed_9_img', 'breed_10', 'breed_10_img')

    user_schema = UserSchema()
    users_schema = UserSchema(many=True)

class Dog(db.Model, UserMixin):
    __tablename__ = 'dog'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.String(50), nullable=False)
    org_id = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String, nullable=False)
    dog_url = db.Column(db.String(200), nullable=False)
    age = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    city_state = db.Column(db.String(100), nullable=False)
    dog_zip_code = db.Column(db.String(10), nullable=False)

    def __init__(self, api_dog_id, api_org_id, status, name, dog_url, age, breed, color, city_state, dog_zip_code):
        self.api_id = api_dog_id
        self.org_id = api_org_id
        self.status = status
        self.name = name
        self.dog_url = dog_url
        self.age = age
        self.breed = breed
        self.color = color
        self.city_state = city_state
        self.dog_zip_code = dog_zip_code

    class DogSchema(ma.Schema):
        class Meta:
            fields = ('id', 'api_dog_id', 'api_org_id', 'status', 'name', 'dog_url',
                      'age', 'breed', 'color', 'sex', 'city_state', 'dog_zip_code')

    dog_schema = DogSchema()
    dogs_schema = DogSchema(many=True)

# class Org(db.Model, UserMixin):
#     __tablename__ = 'org'
#     id = db.Column(db.Integer, primary_key=True)
#     dog_id = db.Column(db.String(50), nullable=False)
#     api_org_id = db.Column(db.String(50), nullable=False)
