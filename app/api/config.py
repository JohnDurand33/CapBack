import os
from dotenv import load_dotenv

load_dotenv()

class Config():
    FLASK_APP = os.environ.get("FLASK_APP")
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False 
    SECRET_KEY=os.environ.get("SECRET_KEY")
