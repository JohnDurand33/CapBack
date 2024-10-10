import requests
import json
import os
import time
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from flask import current_app
from app.models import Dog, Org, fav_dog, db
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from typing import Set, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


class DogDataFetcher:
    def __init__(self, app):
        self.app = app
        self.api_key = os.getenv('RESCUE_KEY')
        if not self.api_key:
            logger.error(
                "API key is not set. Please set the RESCUE_KEY environment variable.")
            raise ValueError(
                "API key is not set. Please set the RESCUE_KEY environment variable.")
        logger.info("DogDataFetcher initialized with API key.")

    def fetch_org_data_from_api(self, result_start, batch_size):
        logger.info(f"Fetching organization data from API with start: {result_start} and batch size: {batch_size}")
        payload = {
            "apikey": self.api_key,
            "objectType": "orgs",
            "objectAction": "publicSearch",
            "search": {
                "resultStart": result_start,
                "resultLimit": batch_size,
                "resultOrder": "asc",
                "calcFoundRows": "Yes",
                "fields": [
                    "orgID", "orgName", "orgCity", "orgState", "orgEmail",
                    "orgAdoptionUrl", "orgWebsiteUrl", "orgFacebookUrl", "orgPostalcode"
                ]
            }
        }
        url = 'https://api.rescuegroups.org/http/v2.json'
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(
                url=url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            logger.info(f"Organization fetch complete. Response status code: {response.status_code}")
            data = response.json().get('data', {})
            if not data:
                logger.warning("Fetched organization data is empty.")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching organization data from API: {e}")
            logger.warning("Returning empty dictionary due to fetch failure.")
            return {}

    def fetch_dog_data_from_api(self, result_start, batch_size):
        logger.info(f"Fetching dog data from API with start: {result_start} and batch size: {batch_size}")
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
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(
                url=url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            logger.info(f"Dog fetch complete. Response status code: {response.status_code}")
            return response.json().get('data', {})
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching dog data from API: {e}")
            return {}

    def update_org_data(self, data, db_orgs, fetched_org_ids):
        logger.info(f"Updating organization data, batch size: {len(data)}")
        new_orgs= []

        with self.app.app_context():
            for api_id, org_data in data.items():
                fetched_org_ids.add(api_id)

                if api_id in db_orgs:
                    existing_org = db_orgs[api_id]
    
                    if (existing_org.name != org_data.get('orgName') or
                            existing_org.city != org_data.get('orgCity') or
                            existing_org.state != org_data.get('orgState') or
                            existing_org.email != org_data.get('orgEmail') or
                            existing_org.adoption_url != org_data.get('orgAdoptionUrl') or
                            existing_org.website_url != org_data.get('orgWebsiteUrl') or
                            existing_org.fb_url != org_data.get('orgFacebookUrl') or
                            existing_org.org_zip_code != org_data.get('orgPostalcode')):
                        existing_org.name = org_data.get('orgName')
                        existing_org.city = org_data.get('orgCity')
                        existing_org.state = org_data.get('orgState')
                        existing_org.email = org_data.get('orgEmail')
                        existing_org.adoption_url = org_data.get('orgAdoptionUrl')
                        existing_org.website_url = org_data.get('orgWebsiteUrl')
                        existing_org.fb_url = org_data.get('orgFacebookUrl')
                        existing_org.org_zip_code = org_data.get('orgPostalcode')
                        logger.info(f"Updated organization: {existing_org}")

                else:   
                    existing_org = Org.query.filter_by(api_id=org_data.get('orgID')).first()
                    if not existing_org:
                        new_org = Org(
                            api_id=org_data.get('orgID'),
                            name=org_data.get('orgName'),
                            city=org_data.get('orgCity'),
                            state=org_data.get('orgState'),
                            email=org_data.get('orgEmail'),
                            adoption_url=org_data.get('orgAdoptionUrl'),
                            website_url=org_data.get('orgWebsiteUrl'),
                            fb_url=org_data.get('orgFacebookUrl'),
                            org_zip_code=org_data.get('orgPostalcode')
                        )
                        new_orgs.append(new_org)
                        logger.info(f"Added new organization: {new_org}")

            try:
                if new_orgs:
                    db.session.add_all(new_orgs)
                    db.session.commit()
                    logger.info(f"Added {len(new_orgs)} new organizations.")
            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"IntegrityError occurred while adding organizations: {e}")

    def delete_unavailable_orgs(self, db_orgs: dict, fetched_org_ids: Set[str]):
        with self.app.app_context():
            db_org_ids = set(db_orgs.keys())
            ids_to_delete: Set[str] = db_org_ids - fetched_org_ids

            if ids_to_delete:
                logger.info(f"Deleting {len(ids_to_delete)} organizations that are no longer available.")

                Org.query.filter(Org.api_id.in_(ids_to_delete)).delete(synchronize_session=False)
                db.session.commit()
                logger.info("All deletions committed successfully.")
            else:
                logger.info("No organizations found for deletion.")

    def update_dog_data(self, data, db_dogs, fetched_ids, fetched_org_ids):
        logger.info(f"Processing dog data, batch size: {len(data)}")
        new_dogs = []

        with self.app.app_context():
            for api_id, dog_data in data.items():
                if api_id in fetched_ids:
                    try:
                        if api_id in db_dogs:
                            db_dog = db_dogs[api_id]
                            if db_dog.status != "1":
                                logger.info(f"Deleting dog with id {db_dog.api_id} as its status changed.")
                                db.session.delete(db_dog)
                        else:
                            if dog_data.get('animalOrgID') in fetched_org_ids:
                                city, state = dog_data.get('animalLocationCitystate').split(', ')
                                new_dog = Dog(
                                    api_id=dog_data.get('animalID'),
                                    org_id=dog_data.get('animalOrgID'),
                                    status=dog_data.get('animalStatusID'),
                                    name=dog_data.get('animalName'),
                                    img_url=dog_data.get('animalThumbnailUrl'),
                                    age=dog_data.get('animalAgeString'),
                                    breed=dog_data.get('animalBreed'),
                                    color=dog_data.get('animalColor'),
                                    sex=dog_data.get('animalSex'),
                                    city=city,
                                    state=state,
                                    dog_zip_code=dog_data.get('animalLocation')
                                )
                                new_dogs.append(new_dog)
                                logger.info(f"Added new dog: {new_dog}")
                            else:
                                fetched_ids.remove(api_id)
                                logger.warning(f"Skipping addition of dog with ID {api_id} because corresponding org ID {dog_data.get('animalOrgID')} does not exist.")
                    except Exception as e:
                        fetched_ids.remove(api_id)
                        logger.warning(f"Error processing dog with API ID {api_id}: {e}")

            if new_dogs:
                try:
                    db.session.add_all(new_dogs)
                    db.session.commit()
                    logger.info(f"Added {len(new_dogs)} new dogs.")
                except IntegrityError as e:
                    db.session.rollback()
                    logger.error(f"IntegrityError occurred while adding dogs: {e}")

    def delete_unavailable_dogs(self, db_dogs, fetched_ids):
        current_ids = set(db_dogs.keys())
        ids_to_delete = current_ids - fetched_ids
        if ids_to_delete:
            logger.info(f"Deleting {len(ids_to_delete)} dogs that are no longer available")
            Dog.query.filter(Dog.api_id.in_(ids_to_delete)).delete(synchronize_session=False)
            db.session.commit()
        else:
            logger.info("No dogs found for deletion.")

    def stop_scheduler(self):
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    def fetch_and_save_data(self):
        logger.info("Job fetch_and_save_data started")
        with self.app.app_context():
            logger.info("Starting to fetch and save data")

            # Fetch and update organization data
            result_start = 0
            batch_size = 1000
            fetched_org_ids = set()
            db_orgs = {org.api_id: org for org in Org.query.all()}
            logger.info(f"Initial count of orgs in database: {len(db_orgs)}")

            while True:
                logger.info(f"Fetching organization batch starting from {result_start}")
                org_data = self.fetch_org_data_from_api(
                    result_start, batch_size)
                if not org_data:
                    logger.info("No more organization data to fetch.")
                    break
                fetched_org_ids.update(org_data.keys())
                logger.info(f"Fetched Org IDs so far: {fetched_org_ids}")
                self.update_org_data(org_data, db_orgs, fetched_org_ids)
                result_start += batch_size
                time.sleep(1)

            # Fetch and update dog data
            result_start = 0
            fetched_ids = set()
            db_dogs = {dog.api_id: dog for dog in Dog.query.all()}
            logger.info(f"Initial count of dogs in database: {len(db_dogs)}")

            while True:
                logger.info(f"Fetching dog batch starting from {result_start}")
                dog_data = self.fetch_dog_data_from_api(
                    result_start, batch_size)
                if not dog_data:
                    logger.info("No more dog data to fetch.")
                    break
                fetched_ids.update(dog_data.keys())
                logger.info(f"Fetched IDs so far: {fetched_ids}")
                self.update_dog_data(dog_data, db_dogs, fetched_ids, fetched_org_ids)
                result_start += batch_size
                time.sleep(1)

            logger.info(f"Current DB dog count: {len(db_dogs)}")
            self.delete_unavailable_dogs(db_dogs, fetched_ids)
            self.stop_scheduler()
            logger.info("Finished shutting down")


def start_scheduler(app):
    fetcher = DogDataFetcher(app)

    trigger = CronTrigger(day='*/7', hour=1)
    # trigger = DateTrigger(run_date=datetime.now() + timedelta(minutes=1))

    scheduler.add_job(fetcher.fetch_and_save_data,trigger=trigger, max_instances=1)
    scheduler.start()
    logger.info("Scheduler started")
