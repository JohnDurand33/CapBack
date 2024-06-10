import requests
import json
import os
import time
from app.models import Dog, Org, db
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


class DogDataFetcher:
    def __init__(self, app):
        self.app = app
        self.api_key = os.getenv('RESCUE_KEY')
        if not self.api_key:
            print("API key is not set. Please set the RESCUE_KEY environment variable.")
            raise ValueError(
                "API key is not set. Please set the RESCUE_KEY environment variable.")

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
            'Content-Type': 'application/json'
        }

        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        logger.info(f"Fetch complete. Response status code: {response.status_code}")
        print(f"Fetch complete. Response status code: {response.status_code}")
        return response.json().get('data', {})

    def process_animal_data(self, data, db_dogs, fetched_ids):
        new_dogs = []
        new_org_ids = set()


        # First, gather and prepare organization entries
        for api_id, animal in data.items():
            org_id = animal.get('animalOrgID')
            existing_org = db.session.query(
                Org).filter_by(api_id=org_id).first()
            if not existing_org and org_id not in new_org_ids:
                logger.info(f"Organization ID {org_id} does not exist in the Org table. Adding new organization with id {org_id}")
                print(f"Organization ID {org_id} does not exist in the Org table. Adding new organization with id {org_id}")
                new_org_id_entry = Org(api_id=org_id)
                db.session.add(new_org_id_entry)
            new_org_ids.add(org_id)

        # Commit all new organizations to the database
        if new_org_ids:
            try:
                db.session.commit()
                logger.info(f"Added {len(new_org_ids)} new organizations.")
                print(f"Added {len(new_org_ids)} new organizations.")
            except IntegrityError as e:
                db.session.rollback()
                logger.error(
                    f"IntegrityError occurred while adding organizations: {e}")
                print(
                    f"IntegrityError occurred while adding organizations: {e}")
                return  

        # Prepare dog entries
        for api_id, animal in data.items():
            fetched_ids.add(api_id)

            if api_id in db_dogs:
                dog = db_dogs[api_id]
                if dog.status != "1":  # Status has changed, remove the dog
                    logger.info(f"Deleting dog with id {dog.api_id} as its status changed.")
                    print(f"Deleting dog with id {dog.api_id} as its status changed.")
                    db.session.delete(dog)
            else:
                city, state = animal.get('animalLocationCitystate').split(', ')
                dog = Dog(
                    api_id=animal.get('animalID'),
                    org_id=animal.get('animalOrgID'),
                    status=animal.get('animalStatusID'),
                    name=animal.get('animalName'),
                    img_url=animal.get('animalThumbnailUrl'),
                    age=animal.get('animalAgeString'),
                    breed=animal.get('animalBreed'),
                    color=animal.get('animalColor'),
                    sex=animal.get('animalSex'),
                    city=city,
                    state=state,
                    dog_zip_code=animal.get('animalLocation')
                )
                new_dogs.append(dog)

        # Commit all new dogs to the database
        if new_dogs:
            try:
                db.session.add_all(new_dogs)
                db.session.commit()
                logger.info(f"Added {len(new_dogs)} new dogs.")
                print(f"Added {len(new_dogs)} new dogs.")
            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"IntegrityError occurred while adding dogs: {e}")
                print(f"IntegrityError occurred while adding dogs: {e}")

    def delete_unavailable_dogs(self, db_dogs, fetched_ids):
        current_ids = set(db_dogs.keys())
        ids_to_delete = current_ids - fetched_ids
        dogs_to_delete = Dog.query.filter(Dog.api_id.in_(ids_to_delete)).all()

        if dogs_to_delete:
            logger.info(f"Deleting {len(dogs_to_delete)} dogs that are no longer available")
            print(f"Deleting {len(dogs_to_delete)} dogs that are no longer available")
            for dog in dogs_to_delete:
                db.session.delete(dog)
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
            print("Starting to fetch and save dogs information")

            fetched_ids = set()
            logger.info("Querying dog id information from database")
            print("Querying dog id information from database")
            db_dogs = {dog.api_id: dog for dog in Dog.query.all()}
            logger.info(
                f"Query to dict -> 'api_id:dog' info -> db_dogs is complete. Initial count of dogs in database: {len(db_dogs)}")
            print(
                f"Query to dict -> 'api_id:dog' info -> db_dogs is complete. Initial count of dogs in database: {len(db_dogs)}")

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
                    logger.info("No more data to fetch.")
                    print("No more data to fetch.")
                    break

                self.process_animal_data(data, db_dogs, fetched_ids)
                logger.info(f"Completed batch, result start: {result_start}")
                print(f"Completed batch, result start: {result_start}")

                result_start += batch_size
                time.sleep(1)

            self.delete_unavailable_dogs(db_dogs, fetched_ids)
        print("Job fetch_and_save_dogs completed")
        self.stop_scheduler()
        print("Finished shutting down")


def start_scheduler(app):
    fetcher = DogDataFetcher(app)
    start_time = datetime.now() + timedelta(minutes=1)
    trigger = DateTrigger(run_date=start_time)
    # trigger = CronTrigger(hour=1, minute=0, day='1/2')
    scheduler.add_job(fetcher.fetch_and_save_dogs,trigger=trigger, max_instances=1)
    scheduler.start()
    print("Scheduler started")
    logger.info("Scheduler started")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        start_scheduler(app)
