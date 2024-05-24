from flask import Blueprint, request, jsonify
from helpers import token_required
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from pyzipcode import ZipCodeDatabase
from . import api


# @api.route('/breedsearch', methods=['GET'])
# @token_required
# def searchdogs():
    # logic to use breeds_list sent from the client to search for dogs in my database