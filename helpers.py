from functools import wraps
from flask import request, jsonify, json
import decimal
from app.models import User
from datetime import datetime, timezone


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_header = request.headers.get('Authorization')
        token = token_header.split(' ')[1] if token_header else None

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        user = User.query.filter_by(token=token).first()
        if user is None:
            return jsonify({'message': 'User not found'}), 401

        if user.token_expiry is None or user.token_expiry < datetime.now(timezone.utc):
            return jsonify({'message': 'Token is invalid or expired!'}), 401

        return f(user, *args, **kwargs)
    return decorated

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(JSONEncoder, self).default(obj)
