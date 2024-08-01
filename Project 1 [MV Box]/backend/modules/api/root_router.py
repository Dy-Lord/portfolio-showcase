import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.modules.api.routes.public.general import general_api_router
from backend.modules.app.core import AppCore
from backend.modules.db.db_engine import DBEngine
from backend.modules.db.mongo_engine import MongoEngine
from backend.modules.tools import sprint, Colors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']

BUILD_TYPE = os.environ['BUILD_TYPE']
WEB_APP_HOST = os.environ['WEB_APP_HOST']


@asynccontextmanager
async def lifespan(app: FastAPI):
    marker = 'RootRouter'
    dev_mode = False
    if BUILD_TYPE == 'DEV':
        sprint('[WARNING] API has been launched in the DEV MODE. Change DEV_MODE .env variable to PRODUCTION',
               Colors.light_yellow)
        dev_mode = True

    app.mongo_engine = MongoEngine(host=MONGO_HOST, username=MONGO_USER, password=MONGO_PASSWORD, marker=marker)
    app.db_engine = DBEngine(db_engine=app.mongo_engine)
    app.app_core = AppCore(db_engine=app.db_engine, dev_mode=dev_mode)

    public_routes_prefix = '/public'
    app.include_router(general_api_router, prefix=public_routes_prefix)

    yield

    app.mongo_engine.__del__()
    app.app_core.__del__()


if BUILD_TYPE == 'DEV':
    docs_url = "/docs"
    redoc_url = '/redocs'
else:
    docs_url = None
    redoc_url = None


api = FastAPI(title='MV Box Playlists API',
              version='0.0.1',
              lifespan=lifespan,
              docs_url=docs_url,
              redoc_url=redoc_url)
api.add_middleware(CORSMiddleware,
                   allow_origins=[WEB_APP_HOST,
                                  'http://localhost:3000',
                                  'http://127.0.0.1:3000'],
                   allow_credentials=True,
                   allow_methods=['*'],
                   allow_headers=['*'])


if __name__ == '__main__':
    uvicorn.run(api, host='0.0.0.0', port=8000)
