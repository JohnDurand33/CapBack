from flask import Blueprint, request, jsonify, render_template
from helpers import token_required
from app.models import User, db
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from . import api


@api.route('/')
def getdata():
    return {'yee': 'naw'}
