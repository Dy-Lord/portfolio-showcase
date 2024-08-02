import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modules.insights.aggregation import AggregationEngine
from modules.api.routes.public.auth import auth_api_router
from modules.api.routes.public.insights import insights_api_router as public_insights_api_router
from modules.api.routes.protected.insights import insights_api_router as protected_insights_api_router
from modules.api.routes.protected.client import client_api_router
from modules.app.config import ConfigManager
from modules.app.user import UserManager
from modules.app.verification import EmailVerification, PasswordResetVerification
from modules.db.engine import MongoEngine
from modules.email_service.engine import MailGunEngine
from modules.tools import CacheStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']
MAILGUN_API_KEY = os.environ['MAILGUN_API_KEY']
WEB_APP_ENDPOINT = os.environ['WEB_APP_ENDPOINT']


tags_metadata = [
    {
        'name': 'Entries',
        'description': '**Public entry endpoints**'
    },
    {
        'name': 'Client',
        'description': '**Client endpoints**'
    },
    {
        'name': 'Insights',
        'description': '**Insights endpoints**'
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    marker = 'APICore'
    app.user_manager = UserManager(marker=marker)
    app.mongo_db = MongoEngine(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PASSWORD,
                               marker=marker)
    app.email_verification = EmailVerification(marker=marker)
    app.password_reset_verification = PasswordResetVerification(marker=marker)
    app.email_service = MailGunEngine(api_key=MAILGUN_API_KEY, marker=marker)
    app.aggregation_service = AggregationEngine()
    app.config_manager = ConfigManager()
    app.cache = CacheStorage()

    # TODO add public prefix
    public_route_prefix = ''
    app.include_router(auth_api_router, prefix=public_route_prefix)
    app.include_router(public_insights_api_router, prefix=public_route_prefix)

    protected = '/protected'
    app.include_router(client_api_router, prefix=protected)
    app.include_router(protected_insights_api_router, prefix=protected)

    yield

    app.user_manager.__del__()
    app.mongo_db.__del__()
    app.email_verification.__del__()
    app.password_reset_verification.__del__()
    app.email_service.__del__()
    app.aggregation_service.__del__()
    app.config_manager.__del__()
    app.cache.__del__()


api = FastAPI(title='CryptoInsight API',
              description='CryptoInsight API',
              version='0.0.1',
              openapi_tags=tags_metadata,
              lifespan=lifespan)
api.add_middleware(CORSMiddleware,
                   allow_origins=['http://localhost', WEB_APP_ENDPOINT],
                   allow_methods=['*'],
                   allow_headers=['*'])


if __name__ == '__main__':
    uvicorn.run(api, host="0.0.0.0", port=8000)
