from secrets import token_hex
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_login import UserMixin
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func

ma = Marshmallow()
db = SQLAlchemy()

# Many-to-Many relationship table for User and Dog
fav_dog = db.Table('fav_dog',
                   db.Column('user_id', db.Integer, db.ForeignKey(
                       'user.id'), primary_key=True),
                   db.Column('dog_id', db.String(50), db.ForeignKey(
                       'dog.api_id'), primary_key=True)
                   )


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    state = db.Column(db.String(10), default='', nullable=False)
    zip_code = db.Column(db.String(10), default='', nullable=False)
    user_created = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    token = db.Column(db.String(256), default='', nullable=True)
    fav_breeds = db.Column(JSON, default=[])
    dogs = db.relationship('Dog', secondary=fav_dog, backref='users', lazy=True)


#Makes the token check method much easier
def ensure_timezone_aware(mapper, connection, target):
    if target.user_created is not None and target.user_created.tzinfo is None:
        target.user_created = target.user_created.replace(tzinfo=timezone.utc)

event.listen(User, 'before_insert', ensure_timezone_aware)
event.listen(User, 'before_update', ensure_timezone_aware)


class Dog(db.Model, UserMixin):
    __tablename__ = 'dog'
    api_id = db.Column(db.String(50), primary_key=True)
    org_id = db.Column(db.String(50), db.ForeignKey(
        'org.api_id'), nullable=False)
    status = db.Column(db.String(100), default='', nullable=False)
    name = db.Column(db.String, default='', nullable=False)
    img_url = db.Column(db.String(200), default='', nullable=True)
    age = db.Column(db.String(50), default='', nullable=True)
    breed = db.Column(db.String(255), default='', nullable=False)
    color = db.Column(db.String(100), default='', nullable=True)
    sex = db.Column(db.String(10), default='', nullable=True)
    city = db.Column(db.String(100), default='', nullable=True)
    state = db.Column(db.String(10), default='', nullable=True)
    dog_zip_code = db.Column(db.String(10), default='', nullable=True)


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


class DogSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Dog
        load_instance = True


class OrgSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Org
        load_instance = True

class UserSchema(ma.SQLAlchemyAutoSchema):
    dogs = ma.Nested(DogSchema, many=True)  

    class Meta:
        model = User
        load_instance = True


user_schema = UserSchema()
users_schema = UserSchema(many=True)
dog_schema = DogSchema()
dogs_schema = DogSchema(many=True)
org_schema = OrgSchema()
orgs_schema = OrgSchema(many=True)
