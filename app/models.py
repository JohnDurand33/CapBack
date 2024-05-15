from secrets import token_hex
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from flask_marshmallow import Marshmallow
from flask_login import UserMixin
from flask_login import LoginManager

login_manager = LoginManager()
ma = Marshmallow()
db = SQLAlchemy()

fav_dog = db.Table('fav_dog',
                   db.Column('user_id', db.Integer, db.ForeignKey(
                       'user.id'), primary_key=True),
                   db.Column('dog_id', db.String(50), db.ForeignKey(
                       'dog.api_id'), primary_key=True)
                   )


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(50), default='', nullable=False, unique=True)
    username = db.Column(db.String(50), default='',
                         nullable=False, unique=True)
    email = db.Column(db.String(100), default='', nullable=False, unique=True)
    password = db.Column(db.String, default='', nullable=False)
    zip_code = db.Column(db.String(10), default='', nullable=False)
    user_created = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    token = db.Column(db.String, default='', unique=True)
    token_expiry = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)
    dogs = db.relationship('Dog', secondary=fav_dog,
                           backref='users', lazy=True)

class UserSchema(ma.Schema):
        class Meta:
            fields = ('id', 'f_name', 'username', 'email', 'password',
                    'zip_code', 'user_created', 'token', 'token_expiry')


class Dog(db.Model, UserMixin):
    __tablename__ = 'dog'
    api_id = db.Column(db.String(50), primary_key=True)
    org_id = db.Column(db.String(50), db.ForeignKey(
        'org.api_id'), default="", nullable=True) 
    status = db.Column(db.String(100), default='', nullable=True)
    name = db.Column(db.String, default='', nullable=True)
    dog_url = db.Column(db.String(200), default='', nullable=True)
    age = db.Column(db.String(50), default='', nullable=True)
    breed = db.Column(db.String(100), default='', nullable=True)
    color = db.Column(db.String(100), default='', nullable=True)
    sex = db.Column(db.String(10), default='', nullable=True)
    city_state = db.Column(db.String(100), default='', nullable=True)
    dog_zip_code = db.Column(db.String(10), default='', nullable=True)


class DogSchema(ma.Schema):
    class Meta:
        fields = ('api_id', 'org_id', 'status', 'name', 'dog_url',
                  'age', 'breed', 'color', 'sex', 'city_state', 'dog_zip_code')


class Org(db.Model, UserMixin):
    __tablename__ = 'org'
    api_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), default='', nullable=True)
    city = db.Column(db.String(100), default='', nullable=True)
    state = db.Column(db.String(10), default='', nullable=True)
    email = db.Column(db.String(100), default='', nullable=True)
    adoption_url = db.Column(db.String(200), default='', nullable=True)
    website_url = db.Column(db.String(200), default='', nullable=True)
    fb_url = db.Column(db.String(200), default='', nullable=True)
    org_zip_code = db.Column(db.String(10), default='', nullable=True)

# Marshmallow schemas for serialization

class OrgSchema(ma.Schema):
    class Meta:
        fields = ('api_id', 'name', 'city', 'state', 'email',
                  'adoption_url', 'website_url', 'fb_url', 'org_zip_code')








