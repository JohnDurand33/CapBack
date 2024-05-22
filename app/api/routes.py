from flask import Blueprint, request, jsonify
from helpers import token_required
from app.models import db, fav_dog, Org, Dog, User, user_schema, users_schema, dog_schema, dogs_schema, org_schema, orgs_schema
from . import api


@api.route('/')
def getdata():
    return {'yee': 'naw'}
