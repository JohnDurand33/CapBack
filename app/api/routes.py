from flask import Blueprint, request, jsonify
from helpers import token_required
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from pyzipcode import ZipCodeDatabase
from . import api

# zip_db = ZipCodeDatabase()


# def get_state_from_zip(zip_code):
#     try:
#         return zip_db[zip_code].state
#     except KeyError:
#         return "ZIP code not found"
    



# @api.route('/breedsearch', methods=['GET'])
# def getbreeds():
#     breeds = db.session.query(Dog.breed).distinct().all()




