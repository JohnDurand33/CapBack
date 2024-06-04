import datetime
import re
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, request, jsonify
from app.models import Dog, fav_dog, db, dog_schema, User

# Record the start time
start_time = datetime.datetime.now()
print(f"Start time: {start_time}")


class DogMatcher:
    def __init__(self, db_session):
        self.db_session = db_session

    def normalize_breed(self, breed):
        breed = re.sub(r'\(.*?\)', '', breed)
        words = re.findall(r'\b\w+\b', breed.lower())
        words = [word for word in words if word not in {'mix', 'mixed', 'dog'}]
        return words

    def parse_breed_names(self, fav_breeds):
        formatted_breeds = set()
        for breed in fav_breeds:
            try:
                if 'name' in breed:
                    names = self.normalize_breed(breed['name'])
                    formatted_breeds.update(names)
            except Exception as e:
                print(f"Error parsing breed name: breed: {breed}, parsed breed: {names if names else 'error parsing breed'} {e}")
        return formatted_breeds

    def find_matching_dogs(self, user, dogs):
        user_breeds = self.parse_breed_names(user.fav_breeds)
        matched_dogs = set()

        for dog in dogs:
            try:
                dog_breeds = self.normalize_breed(dog.breed)
                if any(breed in dog_breeds for breed in user_breeds):
                    dog_dict = dog_schema.dump(dog)
                    matched_dogs.add(frozenset(dog_dict.items()))
            except Exception as e:
                print(f"Error processing dog {dog.api_id}: {e}")

        return [dict(dog) for dog in matched_dogs]
