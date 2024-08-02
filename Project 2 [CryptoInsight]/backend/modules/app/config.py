import os
from datetime import timedelta, datetime
from enum import Enum

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from modules.db.engine import MongoEngine, MongoKeys
from modules.tools import CacheStorage

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']


class Configs(Enum):
    public_api = 'PublicAPI'
    protected_api = 'ProtectedAPI'
    web_app = 'WebApp'


class PublicAPIConfigModel(BaseModel):
    config_type: str = Field(default=Configs.public_api.value, alias='_id')
    latest_insights_limit: int = 20
    latest_insights_delay_seconds: int = 0
    top_impact_coins_24h_limit: int = 5
    public_highlight_24h_limit: int = 5


class ProtectedAPIConfigModel(BaseModel):
    config_type: str = Field(default=Configs.protected_api.value, alias='_id')
    insights_archive_deep_limit_days: int = 30
    top_impact_coins_limit: int = 5


class WebAPPConfigModel(BaseModel):
    config_type: str = Field(default=Configs.web_app.value, alias='_id')
    base_symbol: str = 'USDT'


class ConfigManager:
    def __init__(self):
        self.mongo_db = MongoEngine(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PASSWORD,
                                    marker='ConfigManager')
        self.cache = CacheStorage(default_expiration=timedelta(hours=1))

    def __del__(self):
        self.cache.__del__()
        self.mongo_db.__del__()

    def rebuild_config(self):
        self.mongo_db.drop_collection(db=MongoKeys.app_db, key=MongoKeys.app_config)
        self.build_config()

    def build_config(self):
        default_configs = [
            PublicAPIConfigModel(),
            ProtectedAPIConfigModel(),
            WebAPPConfigModel()
        ]
        default_configs = [config.model_dump(by_alias=True) for config in default_configs]
        self.mongo_db.insert(db=MongoKeys.app_db, key=MongoKeys.app_config, data=default_configs)

    def get_config(self, config: Configs):
        data = self.cache.get_object(config.value)
        if data is None:
            data = self.mongo_db.find_one(db=MongoKeys.app_db, key=MongoKeys.app_config,
                                          target={'_id': config.value})
            self.cache.add_object(obj_id=config.value, obj=data)
        if config is Configs.public_api:
            return PublicAPIConfigModel.model_validate(data)
        elif config is Configs.protected_api:
            return ProtectedAPIConfigModel.model_validate(data)
        elif config is Configs.web_app:
            return WebAPPConfigModel.model_validate(data)
        return None


if __name__ == '__main__':
    engine = ConfigManager()
    engine.rebuild_config()

