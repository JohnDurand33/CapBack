from flask import Blueprint, request, jsonify
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from helpers import token_required
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from pyzipcode import ZipCodeDatabase
from . import api


@api.route('/api/fav-breeds', methods=['GET'])
@token_required
def get_fav_breeds(user):
    return jsonify(user.fav_breeds)


@api.route('/api/fav-breeds', methods=['POST'])
@token_required
def update_fav_breeds(user):
    data = request.json
    user.fav_breeds = data['fav_breeds']
    db.session.commit()
    return jsonify({'message': 'Favorite breeds updated successfully'}), 200
