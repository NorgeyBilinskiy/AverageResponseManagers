import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

current_directory = os.getcwd()
PATH_PROGRAM = os.path.join(current_directory, 'programm_avarage_response.py')

def run_program():
    try:
        logger.info("Starting the program to calculate the average response time of managers...")
        os.system(f'python {PATH_PROGRAM}')
    except Exception as e:
        logger.error(f"Error occurred while running the program:\n{e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    scheduler.add_job(run_program, CronTrigger(hour='0-23', minute='0', second='0'))
    logger.info("Scheduler for running the program every hour has been successfully initialized.")

    try:
        scheduler.start()
    except Exception as e:
        logger.error(f"An error occurred while starting the scheduler:\n{e}")
