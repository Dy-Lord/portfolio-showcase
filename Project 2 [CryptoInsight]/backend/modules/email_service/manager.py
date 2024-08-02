import os
from enum import Enum

from dotenv import load_dotenv

from modules.db.engine import MongoEngine, MongoKeys

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']


class Tags(Enum):
    client = 'client'

    email_verification = 'email_verification'
    password_reset = 'password_reset'

    info = 'info'
    action = 'action'

    tech = 'tech'
    support = 'support'
    finance = 'finance'
    community = 'community'


class Senders(Enum):
    tech_team = 'us-techdepartment-team-techteam'


class MailManager:
    def __init__(self):
        self.mongo_db = MongoEngine(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PASSWORD,
                                    marker='MailManager')

    def __del__(self):
        self.mongo_db.__del__()

    def get_sender(self, sender: Senders):
        user = self.mongo_db.find_one(db=MongoKeys.email_db, key=MongoKeys.email_users,
                                      target={'slug': sender.value})
        return user

