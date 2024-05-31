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
        result = set()
        for breed in fav_breeds:
            try:
                if 'name' in breed:
                    names = self.normalize_breed(breed['name'])
                    result.update(names)
            except Exception as e:
                print(f"Error parsing breed name: breed: {breed}, parsed breed: {
                      names if names else 'error parsing breed'} {e}")
        return result

    def find_matching_dogs(self, user, dogs):
        user_breeds = self.parse_breed_names(user.fav_breeds)
        matched_dogs = set()

        for dog in dogs:
            try:
                dog_breeds = self.normalize_breed(dog.breed)
                if any(breed in dog_breeds for breed in user_breeds):
                    dog_dict = dog_schema.dump(dog)
                    # Use frozenset to make it hashable
                    matched_dogs.add(frozenset(dog_dict.items()))

                    fav_dog_entry = fav_dog.insert().values(user_id=user.id, dog_id=dog.api_id)
                    self.db_session.execute(fav_dog_entry)
                else:
                    print(f"Dog {dog.api_id} breed '{
                          dog.breed}' did not match any user preferences.")
            except SQLAlchemyError as e:
                self.db_session.rollback()
                print(f"Database error processing dog {dog.api_id}: {e}")
            except Exception as e:
                print(f"Error processing dog {dog.api_id}: {e}")

        self.db_session.commit()
        
        # Record the start time
        end_time = datetime.datetime.now()
        print(f"End time: {end_time}")

        duration = end_time - start_time
        print(f"Duration: {duration}")

        # Convert frozensets back to dicts for the final output
        return [dict(dog) for dog in matched_dogs]
