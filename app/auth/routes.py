from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token
from app.models import db, User
import datetime
import jwt
from ...helpers import token_required, JSONEncoder, basic_auth_required
from ..auth import auth


@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already in use'}), 400

    password_hash = generate_password_hash(password)

    new_user = User(username=username, email=email, password=password_hash)
    db.session.add(new_user)
    db.session.commit()

    token = jwt.encode({
        'public_id': new_user.id,
        'exp': datetime.datetime.now() + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token}), 201
