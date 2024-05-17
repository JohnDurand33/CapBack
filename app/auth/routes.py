from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
)
from app.models import db, User
from datetime import datetime, timedelta, timezone
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

    access_token = create_access_token(identity=email, expires_delta=timedelta(hours=1))
    refresh_token = create_refresh_token(identity=email)

    new_user.token = refresh_token
    new_user.token_expiry = datetime.now(timezone.utc) + timedelta(days=30)
    db.session.commit()

    return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 201