from typing import Annotated
from fastapi import Request, Depends

from backend.modules.app.core import AppCore
from backend.modules.db.db_engine import DBEngine


def get_db_engine(request: Request) -> DBEngine:
    return request.app.db_engine


def get_app_core(request: Request) -> AppCore:
    return request.app.app_core


DBEngineDep = Annotated[DBEngine, Depends(get_db_engine)]
AppCoreDep = Annotated[AppCore, Depends(get_app_core)]
