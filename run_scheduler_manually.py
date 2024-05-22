from app import app, scheduler
import time

print("Starting run_scheduler_manually script")

print(f"SQLALCHEMY_DATABASE_URI in run_scheduler_manually: {app.config['SQLALCHEMY_DATABASE_URI']}")  # Debug print

with app.app_context():
    if not scheduler.running:
        print("Scheduler is not running. Starting scheduler...")
        scheduler.start()
        app.logger.info("Scheduler started manually")
        print("Scheduler started manually")
    else:
        print("Scheduler is already running")



