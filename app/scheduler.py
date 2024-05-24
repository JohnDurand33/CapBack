import requests
import json
import os
import time
from flask import current_app as app
from app.models import Dog, Org, db, dog_schema, dogs_schema, org_schema, orgs_schema
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


class DogDataFetcher:
    def __init__(self, app):
        self.app = app
        self.api_key = self.get_api_key()
        if not self.api_key:
            raise ValueError(
                "API key is not set. Please set the RESCUE_KEY environment variable.")

    def get_api_key(self):
        api_key = os.getenv('RESCUE_KEY')
        if not api_key:
            logger.error(
                "API key is not set. Please set the RESCUE_KEY environment variable.")
            print("API key is not set. Please set the RESCUE_KEY environment variable.")
        return api_key

    def fetch_data_from_api(self, result_start, batch_size):
        payload = {
            "apikey": self.api_key,
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
                        "operation": "equals", "criteria": "1"}
                ],
                "fields": [
                    "animalName", "animalID", "animalOrgID", "animalAgeString", "animalBreed", "animalColor",
                    "animalDescription", "animalLocationDistance", "animalLocationCitystate", "animalLocationState",
                    "animalLocation", "animalStatusID", "animalThumbnailUrl", "animalSex", "animalSpecies"
                ]
            }
        }
        url = 'https://api.rescuegroups.org/http/v2.json'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_key
        }

        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        logger.info(f"Fetch complete. Response status code: {response.status_code}")
        print(f"Fetch complete. Response status code: {response.status_code}")
        return response.json().get('data', {})

    def process_animal_data(self, data, db_dogs, fetched_ids):
        new_dogs = []
        new_orgs = {}
        added_orgs = set()

        for api_id, animal in data.items():
            fetched_ids.add(api_id)
            if animal.get('animalID') in db_dogs:
                dog = db_dogs[animal.get('animalID')]
                if dog.status != "1":
                    logger.info(f"Deleting dog with id {dog.api_id} as its status changed.")
                    print(f"Deleting dog with id {dog.api_id} as its status changed.")
                    db.session.delete(dog)
                    dog_schema.dump(dog)
            else:
                org_id = animal.get('animalOrgID')
                if org_id not in added_orgs:
                    if not db.session.query(Org).filter_by(api_id=org_id).first():
                        logger.info(f"Organization ID {org_id} does not exist in the Org table. Adding new organization with id {org_id}")
                        print(f"Organization ID {org_id} does not exist in the Org table. Adding new organization with id {org_id}")
                        org = Org(api_id=org_id)
                        new_orgs[org_id] = org
                        added_orgs.add(org_id)
                        org_schema.dump(org)
                
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
                new_dogs.append(dog)
                dog_schema.dump(dog)

        if new_orgs:
            if len(new_orgs) == 1:
                org_schema.dump(new_orgs[0])  # Serialize the single new dog
        else:
            orgs_schema.dump(new_dogs)  # Serialize the list of new dogs
            db.session.add_all(new_orgs)
        db.session.commit()

        if new_dogs:
            if len(new_dogs) == 1:
                dog_schema.dump(new_dogs[0])  # Serialize the single new dog
        else:
            dogs_schema.dump(new_dogs)  # Serialize the list of new dogs
            db.session.add_all(new_dogs)
        db.session.commit()

    def delete_unavailable_dogs(self, db_dogs, fetched_ids):
        current_ids = set(db_dogs.keys())
        ids_to_delete = current_ids - fetched_ids
        dogs_to_delete = Dog.query.filter(Dog.api_id.in_(ids_to_delete)).all()

        if dogs_to_delete:
            logger.info(f"Deleting {len(dogs_to_delete)} dogs that are no longer available")
            print(f"Deleting {len(dogs_to_delete)} dogs that are no longer available")
            for dog in dogs_to_delete:
                db.session.delete(dog)
                dog_schema.dump(dog)
            db.session.commit()

    def stop_scheduler(self):
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
        print("Scheduler stopped")


    def fetch_and_save_dogs(self):
        print("Job fetch_and_save_dogs started")
        logger.info("Job fetch_and_save_dogs started")
        with self.app.app_context():
            logger.info("Starting to fetch and save dogs information")
            print("Starting to query and save dogs information")

            fetched_ids = set()
            logger.info("Querying dog id information from database")
            print("Querying dog id information from database")
            db_dogs = {dog.api_id: dog for dog in Dog.query.all()}
            logger.info(f"Query to dict -> 'api_id:dog' info -> db_dogs is complete. Initial count of dogs in database: {len(db_dogs)}")
            print(f"Query to dict -> 'api_id:dog' info -> db_dogs is complete. Initial count of dogs in database: {len(db_dogs)}")

            result_start = 0
            batch_size = 1000

            while True:
                try:
                    data = self.fetch_data_from_api(result_start, batch_size)
                except requests.exceptions.HTTPError as http_err:
                    logger.error(f"HTTP error occurred: {http_err}")
                    print(f"HTTP error occurred: {http_err}")
                    break
                except Exception as err:
                    logger.error(f"Other error occurred: {err}")
                    print(f"Other error occurred: {err}")
                    break

                if not data:
                    logger.info(f"No more data to fetch.")
                    print(f"No more data to fetch.")
                    break

                self.process_animal_data(data, db_dogs, fetched_ids)
                logger.info(f"Completed batch, result start: {result_start}")
                print(f"Completed batch, result start: {result_start}")

                result_start += batch_size
                time.sleep(1)

            self.delete_unavailable_dogs(db_dogs, fetched_ids)
        print("Job fetch_and_save_dogs completed")
        self.stop_scheduler()
        print("Finised shutting down")

def start_scheduler(app):
    fetcher = DogDataFetcher(app)
    # Run every other day at 1 AM
    trigger = CronTrigger(hour=1, minute=0, day="*/2")
    scheduler.add_job(fetcher.fetch_and_save_dogs,trigger=trigger, max_instances=1)
    scheduler.start()
    print("Scheduler started")
    logger.info("Scheduler started")
