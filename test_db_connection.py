from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the DATABASE_URL environment variable
DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URI')
print(f"DATABASE_URL from .env: {DATABASE_URL}")  # Verify the URL

if DATABASE_URL is None or DATABASE_URL == "":
    print("Environment variable SQLALCHEMY_DATABASE_URI not set or empty.")
else:
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as connection:
            print("Connection to the database was successful!")
    except Exception as e:
        print(f"An error occurred: {e}")
