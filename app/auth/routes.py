from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app.models import db, User
from datetime import datetime, timedelta
from .__init import auth


@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    zip_code = data.get('zipCode')

    if not email or not password or not zip_code:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already in use'}), 400

    password_hash = generate_password_hash(password)

    new_user = User(email=email, password=password_hash, zip_code=zip_code)
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)

    new_user.token = refresh_token
    new_user.token_expiry = datetime.now() + timedelta(days=30)
    db.session.commit()

    return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 201


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

    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)

    user.token = refresh_token
    user.token_expiry = datetime.now() + timedelta(days=30)
    db.session.commit()

    return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 200


@auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()

    if not user or user.token != get_jwt()["jti"]:
        return jsonify({'message': 'Invalid refresh token'}), 401

    new_access_token = create_access_token(identity=current_user)

    return jsonify({'access_token': new_access_token}), 200

@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hello, {current_user}! This is a protected route.'})
