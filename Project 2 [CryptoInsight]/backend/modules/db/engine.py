from enum import Enum
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.server_api import ServerApi

from modules.tools import sprint, Colors


class MongoKeys(Enum):
    binance_db = 'binance'
    binance_authors = 'authors'
    binance_news = 'news'
    binance_hot_tags = 'hot_tags'
    binance_fear_index = 'fear_index'
    binance_highest_searched_coins = 'highest_searched_coins'
    binance_jobs = 'jobs'

    openai_db = 'openai'
    openai_config = 'config'

    market_db = 'market'
    market_jobs = 'jobs'
    market_kline = 'klines'

    app_db = 'app'
    app_users = 'users'
    app_email_verification = 'email_verification'
    app_password_reset_verification = 'password_reset_verification'
    app_config = 'config'

    email_db = 'email'
    email_users = 'users'

    insights_db = 'insights'
    insight_hourly_coin_impact = 'hourly_coin_impact'
    insights_daily_coin_impact = 'daily_coin_impact'
    insights_monthly_coin_impact = 'monthly_coin_impact'
    insights_news_insights = 'news_insights'
    insights_news_insights_map = 'news_insights_map'


class MongoEngine:
    def __init__(self, host: str, port: int, username: str, password: str, marker: str = None):
        connection_url = f'mongodb://{quote_plus(username)}:{quote_plus(password)}@{quote_plus(host)}/?retryWrites=true&w=majority'

        self.marker = marker
        sprint(f'[MONGO_DB] [{marker}] [CONNECTING]', Colors.light_green)
        self.engine = MongoClient(host=connection_url, port=port, server_api=ServerApi('1'))

    def __del__(self):
        sprint(f'[MONGO_DB] [{self.marker}] [DISCONNECTING]', Colors.light_red)
        self.engine.close()

    def insert(self, db: MongoKeys, key: MongoKeys, data: list[dict] | dict):
        if data:
            if type(data) is list:
                return self.engine[db.value][key.value].insert_many(data)
            elif type(data) is dict:
                return self.engine[db.value][key.value].insert_one(data)
        return None

    def find_one(self, db: MongoKeys, key: MongoKeys, target: dict, project: dict = None):
        if target is not None:
            return self.engine[db.value][key.value].find_one(filter=target, projection=project)

    def find(self, db: MongoKeys, key: MongoKeys, target: dict, project: dict = None, sort: list[tuple] = None,
             skip: int = 0, limit: int = 0):
        if target is not None:
            return self.engine[db.value][key.value].find(filter=target, projection=project, sort=sort,
                                                         skip=skip, limit=limit)

    def update_one(self, db: MongoKeys, key: MongoKeys, target: dict, update_query: dict, upsert: bool = False):
        if update_query is not None:
            return self.engine[db.value][key.value].update_one(filter=target, update=update_query, upsert=upsert)

    def update_many(self, db: MongoKeys, key: MongoKeys, target: dict, update_query: dict, upsert: bool = False):
        if update_query is not None:
            return self.engine[db.value][key.value].update_many(filter=target, update=update_query, upsert=upsert)

    def delete_one(self, db: MongoKeys, key: MongoKeys, target: dict):
        if target is not None:
            return self.engine[db.value][key.value].delete_one(filter=target)

    def exists(self, db: MongoKeys, key: MongoKeys, target: dict):
        if target is not None:
            return bool(self.engine[db.value][key.value].count_documents(filter=target, limit=1))

    def get_keys(self, db: MongoKeys, key: MongoKeys, target: dict) -> list[str]:
        if target is not None:
            keys = list(self.engine[db.value][key.value].aggregate([{'$match': target},
                                                               {'$project': {'array': {'$objectToArray': '$$ROOT'}}},
                                                               {'$project': {'keys': '$array.k', '_id': 0}}]))
            return keys[0]['keys'] if keys else []

    def drop_collection(self, db: MongoKeys, key: MongoKeys):
        self.engine[db.value][key.value].drop()

