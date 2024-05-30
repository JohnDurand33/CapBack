from flask import Blueprint, request, jsonify
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from helpers import token_required
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from flask_cors import cross_origin
from . import api


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


# @api.route('/updatebreeds', methods=['POST'])
# @token_required
# def update_fav_breeds(user):
#     data = request.json
#     user.fav_breeds = data['fav_breeds']
#     print(f'user.fav_breeds: {user.fav_breeds}')
#     db.session.commit()
#     return jsonify({'message': 'Favorite breeds updated successfully'}), 200
