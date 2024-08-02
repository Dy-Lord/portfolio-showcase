from typing import Annotated

from fastapi import Request, Depends

from modules.insights.aggregation import AggregationEngine
from modules.app.config import ConfigManager
from modules.app.user import UserManager
from modules.app.verification import EmailVerification, PasswordResetVerification
from modules.db.engine import MongoEngine
from modules.email_service.engine import MailGunEngine
from modules.tools import CacheStorage


def get_user_manager(request: Request) -> UserManager:
    return request.app.user_manager


def get_mongo_db_engine(request: Request) -> MongoEngine:
    return request.app.mongo_db


def get_email_verification(request: Request) -> EmailVerification:
    return request.app.email_verification


def get_password_reset_verification(request: Request) -> PasswordResetVerification:
    return request.app.password_reset_verification


def get_cache(request: Request) -> CacheStorage:
    return request.app.cache


def get_email_service(request: Request) -> MailGunEngine:
    return request.app.email_service


def get_aggregation_service(request: Request) -> AggregationEngine:
    return request.app.aggregation_service


def get_config_manager(request: Request) -> ConfigManager:
    return request.app.config_manager


UserManagerDep = Annotated[UserManager, Depends(get_user_manager)]
MongoDBDep = Annotated[MongoEngine, Depends(get_mongo_db_engine)]
EmailVerificationDep = Annotated[EmailVerification, Depends(get_email_verification)]
PasswordResetVerificationDep = Annotated[PasswordResetVerification, Depends(get_password_reset_verification)]
CacheDep = Annotated[CacheStorage, Depends(get_cache)]
EmailServiceDep = Annotated[MailGunEngine, Depends(get_email_service)]
AggregationServiceDep = Annotated[AggregationEngine, Depends(get_aggregation_service)]
ConfigManagerDep = Annotated[ConfigManager, Depends(get_config_manager)]
