from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.client_session import ClientSession
from pymongo.server_api import ServerApi

from backend.modules.db.models import Keys
from backend.modules.tools import sprint, Colors


class MongoEngine:
    def __init__(self, host: str, username: str, password: str, port: int = None, marker: str = None,
                 verbose: bool = True):
        connection_url = f'mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{quote_plus(host)}/?retryWrites=true&w=majority'

        self.verbose = verbose
        self.marker = marker

        if self.verbose:
            sprint(f'[MONGO_DB] [{marker}] [CONNECTING]', Colors.light_green)
        self.engine = MongoClient(host=connection_url, port=port, server_api=ServerApi('1'))
        self.session: ClientSession | None = None

    def __del__(self):
        if self.verbose:
            sprint(f'[MONGO_DB] [{self.marker}] [DISCONNECTING]', Colors.light_red)
        self.abort_session()
        self.engine.close()

    def start_session(self):
        self.abort_session()
        self.session = self.engine.start_session()
        self.session.start_transaction()

    def abort_session(self):
        if self.session is not None:
            self.session.abort_transaction()
            self.session = None

    def insert(self, db: Keys, key: Keys, data: list[dict] | dict):
        if data:
            if type(data) is list:
                return self.engine[db.value][key.value].insert_many(data, session=self.session)
            elif type(data) is dict:
                return self.engine[db.value][key.value].insert_one(data, session=self.session)
        return None

    def find_one(self, db: Keys, key: Keys, target: dict, project: dict = None):
        if target is not None:
            return self.engine[db.value][key.value].find_one(filter=target, projection=project, session=self.session)

    def find(self, db: Keys, key: Keys, target: dict = None, project: dict = None, sort: list[tuple] = None,
             skip: int = 0, limit: int = 0):
        if target is not None:
            return self.engine[db.value][key.value].find(filter=target if target else {},
                                                         projection=project, sort=sort,
                                                         skip=skip, limit=limit, session=self.session)

    def update_one(self, db: Keys, key: Keys, target: dict, update_query: dict, upsert: bool = False):
        if update_query is not None:
            return self.engine[db.value][key.value].update_one(filter=target, update=update_query, upsert=upsert,
                                                               session=self.session)

    def update_many(self, db: Keys, key: Keys, target: dict, update_query: dict, upsert: bool = False):
        if update_query is not None:
            return self.engine[db.value][key.value].update_many(filter=target, update=update_query, upsert=upsert,
                                                                session=self.session)

    def delete_one(self, db: Keys, key: Keys, target: dict):
        if target is not None:
            return self.engine[db.value][key.value].delete_one(filter=target, session=self.session)

    def exists(self, db: Keys, key: Keys, target: dict):
        if target is not None:
            return bool(self.engine[db.value][key.value].count_documents(filter=target, limit=1, session=self.session))

    def count(self, db: Keys, key: Keys, target: dict):
        if target is not None:
            return self.engine[db.value][key.value].count_documents(filter=target, session=self.session)

    def get_keys(self, db: Keys, key: Keys, target: dict) -> list[str]:
        if target is not None:
            keys = list(self.engine[db.value][key.value].aggregate([{'$match': target},
                                                                   {'$project': {'array': {'$objectToArray': '$$ROOT'}}},
                                                                   {'$project': {'keys': '$array.k', '_id': 0}}],
                                                                   session=self.session))
            return keys[0]['keys'] if keys else []

    def drop_collection(self, db: Keys, key: Keys):
        self.engine[db.value][key.value].drop(session=self.session)

