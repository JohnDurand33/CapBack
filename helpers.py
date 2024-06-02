from functools import wraps
from flask import request, jsonify, json
import decimal
from app.models import User, db, Dog, Org, fav_dog, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from datetime import datetime, timezone
import jwt
from functools import wraps
from flask import request, jsonify, current_app as app


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token_header = request.headers['Authorization']
                Bearer, token = token_header.split(' ')
                print(f'Received token: {token}')
            except ValueError:
                print('Token format is invalid')
                return jsonify({'message': 'Token format is invalid!'}), 401

        if not token:
            print('Token is missing')
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=["HS256"])
            print(f'Decoded token data: {data}')
            user_id = data.get('user_id')
            if not user_id:
                print('Token data is invalid: user_id not found')
                return jsonify({'message': 'Token data is invalid!'}), 401

            user = User.query.filter_by(id=user_id).first()
            if not user:
                print('User not found')
                return jsonify({'message': 'User not found!'}), 403
        except jwt.ExpiredSignatureError:
            print('Token has expired')
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            print('Token is invalid')
            return jsonify({'message': 'Token is invalid!'}), 402

        return f(user, *args, **kwargs)
    return decorated

# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         if 'Authorization' in request.headers:
#             token_header = request.headers['Authorization']
#             token = token_header.split(' ')[1]

#         if not token:
#             return jsonify({'message': 'Token is missing!'}), 401

#         user = User.query.filter_by(token=token).first()
#         if user is None:
#             return jsonify({'message': 'User not found'}), 401

#         if user.token_expiry is None or user.token_expiry < datetime.now(timezone.utc):
#             return jsonify({'message': 'Token is invalid or expired!'}), 401

#         print(f'token authenticated! User: {user}')
#         return f(user, *args, **kwargs)
#     return decorated

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(JSONEncoder, self).default(obj)
