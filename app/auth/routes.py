from functools import wraps
from flask import request, jsonify, current_app as app
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from datetime import datetime, timedelta, timezone
from helpers import token_required
from .__init__ import auth
import secrets
from flask_cors import cross_origin
from flask import make_response


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

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'email' : user.email,
        'state' : user.state,
        'zip_code' : user.zip_code
    }, app.config['SECRET_KEY'], algorithm="HS256")

    user.token = token
    db.session.commit()

    return jsonify({'token': user.token, 'zip_code': user.zip_code, 'state': user.state}), 200


@auth.route('/refresh', methods=['POST'])
def refresh_token():
    token = request.json.get('token')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401

    try:
        print(f'Received Token: {token}')  # Log the received token
        # Decode the token without verifying the expiration to extract user_id
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"], options={"verify_exp": False})
        print(f'Decoded Data: {data}')  # Log the decoded data
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'message': 'Invalid token data!'}), 401

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'message': 'User not found!'}), 401

        # Create a new token
        new_token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'email': user.email,
            'state': user.state,
            'zip_code': user.zip_code
        }, app.config['SECRET_KEY'], algorithm="HS256")
        print(f'New Token: {new_token}')  # Log the new token

        user_schema.dump(user)
        db.session.commit()
        print(f'New token sotred in database to {user.email}: {user.token}')

        return jsonify({'token': new_token}), 200
    except jwt.InvalidTokenError as e:
        print(f'Invalid Token Error: {e}')  # Log the invalid token error
        return jsonify({'message': 'Token is invalid!'}), 401


@auth.route('/logout', methods=['POST'])
@token_required
def logout(user):
    user.token = None
    user_schema.dump(user)
    db.session.commit()

    return jsonify({'message': 'Logged out successfully'}), 200



