from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from datetime import datetime, timedelta, timezone
from helpers import token_required
from .__init__ import api
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import cross_origin
from ..auth import DogMatcher


@api.route('/getbreeds', methods=['GET'])
@token_required
def get_fav_breeds(user):
    try:
        print(f'User: {user}')
        print(f'favBreeds: {user.fav_breeds}')
        return jsonify(user.fav_breeds), 200
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'message': 'Internal Server Error'}), 500


@api.route('/updatebreeds', methods=['POST'])
@token_required
def update_fav_breeds(user):
    data = request.json
    user.fav_breeds = data['fav_breeds']
    print(f'user.fav_breeds: {user.fav_breeds}')
    db.session.commit()
    return jsonify({'message': 'Favorite breeds updated successfully'}), 200


@api.route('/matchbreeds', methods=['POST'])
@token_required
def match_dogs(user):
    dogs = Dog.query.filter(Dog.state == user.state).all()
    dog_matcher = DogMatcher(db.session)
    matched_dogs = dog_matcher.find_matching_dogs(user, dogs)
    return jsonify(matched_dogs), 200


@api.route('/favdogs', methods=['POST'])
@token_required
def add_favorite_dog(user):
    try:
        data = request.get_json()
        dog_id = data.get('dog_id')

        if not dog_id:
            return jsonify({"error": "Dog ID is required"}), 400

        existing_entry = db.session.query(fav_dog).filter_by(
            user_id=user.id, dog_id=dog_id).first()
        if existing_entry:
            return jsonify({"error": "Dog already in favorites"}), 400

        new_fav_dog = fav_dog.insert().values(user_id=user.id, dog_id=dog_id)
        db.session.execute(new_fav_dog)
        db.session.commit()

        return jsonify({"message": "Dog added to favorites"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error adding favorite dog"}), 500


@api.route('/favdogs/<int:dog_id>', methods=['DELETE'])
@token_required
def delete_favorite_dog(user, dog_id):
    try:
        # Check if the dog exists in the favorites
        existing_entry = db.session.query(fav_dog).filter_by(
            user_id=user.id, dog_id=dog_id).first()
        if not existing_entry:
            return jsonify({"error": "Dog not found in favorites"}), 404

        db.session.query(fav_dog).filter_by(
            user_id=user.id, dog_id=dog_id).delete()
        db.session.commit()

        return jsonify({"message": "Dog removed from favorites"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error deleting favorite dog"}), 500
