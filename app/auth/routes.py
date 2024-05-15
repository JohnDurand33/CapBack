from flask import Flask, request, jsonify
from ..models import db, User, UserSchema
from werkzeug.security import generate_password_hash
import jwt
import datetime
from ..auth import auth


@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Validate input data (add your validation logic here)

    # Hash the password
    password_hash = generate_password_hash(password)

    # Create new user and add to database
    new_user = User(username=username, email=email,
                    password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    # Generate token
    token = jwt.encode({
        'public_id': new_user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token}), 201
