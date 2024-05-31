from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from datetime import datetime, timedelta, timezone
from helpers import token_required
from .__init__ import auth
import secrets
from flask_cors import cross_origin
from . import DogMatcher


@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    state= data.get('state')
    zip_code = data.get('zip_code')

    if not email or not password or not state or not zip_code:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already in use'}), 400

    password_hash = generate_password_hash(password)
    new_user = User(email=email, password=password_hash, state=state, zip_code=zip_code)
    db.session.add(new_user)
    user_schema.dump(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid email or password'}), 401

    token = secrets.token_hex(16)
    user.token = token
    user.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    user_schema.dump(user)
    db.session.commit()

    return jsonify({'token': user.token}), 200


@auth.route('/logout', methods=['POST'])
@token_required
def logout(user):
    user.token = None
    user.token_expiry = None
    user_schema.dump(user)
    db.session.commit()

    return jsonify({'message': 'Logged out successfully'}), 200


@auth.route('/protected', methods=['GET'])
@token_required
def protected(user):
    return jsonify({'message': 'You are logged in'}), 200


# @auth.route('/getbreeds', methods=['GET'])
# @token_required
# def get_fav_breeds(user):
#     try:
#         print(f'User: {user}')
#         print(f'favBreeds: {user.fav_breeds}')
#         return jsonify(user.fav_breeds), 200
#     except Exception as e:
#         print(f'Error: {e}')
#         return jsonify({'message': 'Internal Server Error'}), 500


# @auth.route('/updatebreeds', methods=['POST'])
# @token_required
# def update_fav_breeds(user):
#     data = request.json
#     user.fav_breeds = data['fav_breeds']
#     print(f'user.fav_breeds: {user.fav_breeds}')
#     db.session.commit()
#     return jsonify({'message': 'Favorite breeds updated successfully'}), 200


# @auth.route('/matchdogs', methods=['POST'])
# @token_required
# def match_dogs(user):
#     dogs = Dog.query.filter(Dog.state == user.state).all()
#     dog_matcher = DogMatcher(db.session)
#     matched_dogs = dog_matcher.find_matching_dogs(user, dogs)
#     return jsonify(matched_dogs), 200

