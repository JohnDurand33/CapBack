from .models import User, Dog, Org, fav_dog, db, ma
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app as app
import requests
import json
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def fetch_and_save_dogs():
    with app.app_context():
        states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
                ]

        api_key = os.getenv('RESCUE_KEY')
        if not api_key:
            logger.error(
                "API key is not set. Please set the RESCUE_KEY environment variable.")
            return

        logger.info("Starting to fetch and save dogs information")
        print("Starting to fetch and save dogs information")

        fetched_ids = set()
        db_dogs = {dog.api_id: dog for dog in Dog.query.all()}
        print(f"Initial count of dogs in database: {len(db_dogs)}")
        dogs_to_delete = set()

        for state in states:
            logger.info(f"Fetching data for state: {state}")
            print(f"Fetching data for state: {state}")
            result_start = 0
            batch_size = 1000
            while True:
                payload = {
                    "apikey": str(api_key),
                    "objectType": "animals",
                    "objectAction": "publicSearch",
                    "search": {
                        "resultStart": result_start,
                        "resultLimit": batch_size,
                        "resultOrder": "asc",
                        "calcFoundRows": "Yes",
                        "filters": [
                            {"fieldName": "animalSpecies",
                                "operation": "equals", "criteria": "Dog"},
                            {"fieldName": "animalStatusID",
                                "operation": "equals", "criteria": "1"},
                            {"fieldName": "animalLocationState",
                                "operation": "equals", "criteria": state}
                        ],
                        "fields": [
                            "animalName", "animalID", "animalOrgID", "animalAgeString", "animalBreed", "animalColor",
                            "animalDescription", "animalLocationDistance", "animalLocationCitystate", "animalLocationState",
                            "animalLocation", "animalStatusID", "animalThumbnailUrl", "animalSex", "animalSpecies"
                        ]
                    }
                }

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': api_key
                }

                try:
                    logger.info(f"Sending request to API for state {state}, result start: {result_start}")
                    print(f"Sending request to API for state {state}, result start: {result_start}")
                    response = requests.post(
                        'https://api.rescuegroups.org/http/v2.json', headers=headers, data=json.dumps(payload))
                    response.raise_for_status()  # Raise an exception for HTTP errors
                except requests.exceptions.HTTPError as http_err:
                    logger.error(f"HTTP error occurred for state {state}, result start {result_start}: {http_err}")
                    print(f"HTTP error occurred for state {state}, result start {result_start}: {http_err}")
                    break  # Exit loop and move to the next state
                except Exception as err:
                    logger.error(f"Other error occurred for state {state}, result start {result_start}: {err}")
                    print(f"Other error occurred for state {state}, result start {result_start}: {err}")
                    break  # Exit loop and move to the next state

                data = response.json().get('data', {})
                if not data:
                    logger.info(f"No more data to fetch for state {state}")
                    print(f"No more data to fetch for state {state}")
                    break  # No more data to fetch for this state

                for api_id, animal in data.items():
                    fetched_ids.add(animal.get('animalID'))
                    if animal.get('animalID') in db_dogs:
                        dog = db_dogs[animal.get('animalID')]
                        if dog.status != "1":
                            logger.info(f"Deleting dog with id {dog.api_id} as its status changed.")
                            print(f"Deleting dog with id {dog.api_id} as its status changed.")
                            db.session.delete(dog)
                    else:
                        logger.info(f"Adding new dog with id {animal.get('animalID')}")
                        print(f"Adding new dog with id {animal.get('animalID')}")
                        dog = Dog(
                            api_id=animal.get('animalID'),
                            org_id=animal.get('animalOrgID'),
                            status=animal.get('animalStatusID'),
                            name=animal.get('animalName'),
                            dog_url=animal.get('animalThumbnailUrl'),
                            age=animal.get('animalAgeString'),
                            breed=animal.get('animalBreed'),
                            color=animal.get('animalColor'),
                            sex=animal.get('animalSex'),
                            city_state=animal.get('animalLocationCitystate'),
                            dog_zip_code=animal.get('animalLocation')
                        )
                        db.session.add(dog)
                db.session.commit()
                logger.info(f"Completed batch for state {state}, result start: {result_start}")
                print(f"Completed batch for state {state}, result start: {result_start}")

                result_start += batch_size
                time.sleep(1)  # Pause to avoid hitting rate limits

        current_ids = set(db_dogs.keys())
        ids_to_delete = current_ids - fetched_ids
        dogs_to_delete.update(Dog.query.filter(
            Dog.api_id.in_(ids_to_delete)).all())

        if dogs_to_delete:
            logger.info(f"Deleting {len(dogs_to_delete)} dogs that are no longer available")
            print(f"Deleting {len(dogs_to_delete)} dogs that are no longer available")
            for dog in dogs_to_delete:
                db.session.delete(dog)
            db.session.commit()

        logger.info("Dog information fetch and save completed")
        print("Dog information fetch and save completed")


# Initialize and start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_save_dogs, 'cron', day='*/1', hour=1, minute=0)
scheduler.start()
print("Scheduler started")
