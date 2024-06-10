from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from datetime import datetime, timedelta, timezone
from helpers import token_required
from .__init__ import api
from sqlalchemy.exc import SQLAlchemyError
from ..DogMatcher import DogMatcher
import random
import requests
import json
import os


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


@api.route('/get_favdogs', methods=["GET", "POST"])
@token_required
def get_favorite_dogs(user):
    try:
        fav_dogs = db.session.query(Dog).join(
            fav_dog).filter_by(user_id=user.id).all()
        print(f'fav_dogs: {fav_dogs}')
        return dogs_schema.jsonify(fav_dogs), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error getting favorite dogs"}), 500

@api.route('/updatebreeds', methods=['POST'])
@token_required
def update_fav_breeds(user):
    data = request.json
    user.fav_breeds = data['fav_breeds']
    print(f'user.fav_breeds: {user.fav_breeds}')
    db.session.commit()
    return jsonify({'message': 'Favorite breeds updated successfully'}), 200

@api.route('/clearbreeds', methods=['DELETE'])
@token_required
def clear_fav_breeds(user):
    user.fav_breeds = []
    db.session.commit()
    return jsonify({'message': 'Favorite breeds cleared successfully'}), 200


@api.route('/randomize_dogs', methods=['POST'])
@token_required
def randomize_dogs(user):
    dogs = Dog.query.filter(Dog.state == user.state).all()
    dog_matcher = DogMatcher(db.session)
    matched_dogs = dog_matcher.find_matching_dogs(user, dogs)
    randomized_dogs = random.shuffle(matched_dogs)
    return jsonify(randomized_dogs), 200


@api.route('/find_dogs', methods=['POST'])
@token_required
def match_dogs(user):
    dogs = Dog.query.filter(Dog.state == user.state).all()
    dog_matcher = DogMatcher(db.session)
    matched_dogs = dog_matcher.find_matching_dogs(user, dogs)
    return jsonify(matched_dogs), 200

@api.route('/add_favdog', methods=['POST'])
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


@api.route('/rem_favdog/<string:api_id>', methods=["DELETE"])
@token_required
def delete_favorite_dog(user, api_id):
    try:

        existing_entry = db.session.query(fav_dog).filter_by(
            user_id=user.id, dog_id=api_id).first()

        if not existing_entry:
            return jsonify({"error": "Dog not found in favorites"}), 404

        db.session.query(fav_dog).filter_by(
            user_id=user.id, dog_id=api_id).delete()
        db.session.commit()

        return jsonify({"message": "Dog removed from favorites"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error deleting favorite dog"}), 500
    
@api.route('/clear_fav_dogs', methods=['DELETE'])
@token_required
def clear_fav_dogs(user):
    try:
        user_fav_entries = db.session.query(fav_dog).filter_by(user_id=user.id).all()
        print(f"User fav entries: {user_fav_entries}")
    
        if user_fav_entries:
            db.session.query(fav_dog).filter_by(user_id=user.id).delete()
            db.session.commit()
            return jsonify({"message": "All dogs removed from favorites"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error deleting favorite dog"}), 500
    
@api.route('/get_org_details/<string:dog_id>', methods=['GET'])
@token_required
def get_org_details(user, dog_id):
    try:
        dog = Dog.query.filter_by(api_id=dog_id).first()
        if not dog:
            return jsonify({"error": "Dog not found"}), 404

        org_id = dog.org_id
        payload = {
            "apikey": os.getenv('RESCUE_KEY'),
            "objectType": "orgs",
            "objectAction": "publicSearch",
            "search": {
                "resultLimit": 1,
                "filters": [
                    {"fieldName": "orgID", "operation": "equals", "criteria": org_id}
                ],
                "fields": ["orgID", "orgEmail"]
            }
        }
        url = 'https://api.rescuegroups.org/http/v2.json'
        headers = {'Content-Type': 'application/json'}

        response = requests.post(
            url=url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        org_data = response.json().get('data', {})
        if not org_data:
            return jsonify({"error": "Organization not found"}), 404

        org_email = next(iter(org_data.values())).get('orgEmail')
        if not org_email:
            return jsonify({"error": "Organization email not found"}), 404

        return jsonify({"orgEmail": org_email}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500
    



