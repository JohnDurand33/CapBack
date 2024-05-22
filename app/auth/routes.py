from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from datetime import datetime, timedelta, timezone
from helpers import token_required
from .__init import auth
import secrets


@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    zip_code = data.get('zip_code')

    if not email or not password or not zip_code:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already in use'}), 400

    password_hash = generate_password_hash(password)
    new_user = User(email=email, password=password_hash, zip_code=zip_code)
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
    return jsonify({'message': f'Hello, {user.email}! This is a protected route.'}), 200


