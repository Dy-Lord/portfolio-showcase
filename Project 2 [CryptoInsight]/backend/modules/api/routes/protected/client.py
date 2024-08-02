from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Security, HTTPException
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from modules.api.auxiliary.dependencies import UserManagerDep, EmailVerificationDep, CacheDep, EmailServiceDep
from modules.api.auxiliary.oauth2 import user_auth
from modules.app.user import UserScope, AccessScopes
from modules.app.verification import VerificationStatus
from modules.email_service.templates import TemplateEngine
from modules.tools import get_scope_description

client_api_router = APIRouter(prefix='/client', tags=['client'])


class EmailVerificationModel(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class UserProfileModel(BaseModel):
    fullname: str
    user_scope: UserScope


@client_api_router.get('/profile', response_model=UserProfileModel, summary='User Profile', description=' ')
def get_profile(user_token: Annotated[dict, Security(user_auth, scopes=[])],
                user_manager: UserManagerDep):
    user = user_manager.get_user_by_token(user_token)
    return UserProfileModel(fullname=user['fullname'],
                            user_scope=UserScope.value_to_object(user['user_scope']))


@client_api_router.post('/email/verify_email', summary='Email Verification', description=get_scope_description([AccessScopes.access_tier_0.value]))
def verify_email(body: EmailVerificationModel,
                 user_token: Annotated[dict, Security(user_auth, scopes=[AccessScopes.access_tier_0.value])],
                 user_manager: UserManagerDep,
                 email_verification: EmailVerificationDep) -> VerificationStatus:
    user = user_manager.get_user_by_token(user_token)
    status = email_verification.verify_code(secret_code=body.code, email=user['email'])
    if status is VerificationStatus.verified:
        user_manager.update_user_scope(user_token=user_token, scope=UserScope.regular)
    return status


@client_api_router.post('/email/request_email_verification', summary='Email Verification Request',
                        description=get_scope_description([AccessScopes.access_tier_0.value]))
def launch_email_verification(user_token: Annotated[dict, Security(user_auth, scopes=[AccessScopes.access_tier_0.value])],
                              user_manager: UserManagerDep,
                              email_verification: EmailVerificationDep,
                              cache: CacheDep,
                              email_service: EmailServiceDep):
    user = user_manager.get_user_by_token(user_token)
    cache_id = f'email_verification_history_{user_token}'
    verification_history = cache.get_object(cache_id)
    if verification_history:
        verification_history['resend_count'] += 1
        if verification_history['resend_count'] > 3:
            retry_time = cache.get_object_expiration_time(cache_id)
            retry_time = str(int((retry_time - datetime.now(timezone.utc)).total_seconds())) if retry_time else 0
            raise HTTPException(http_status.HTTP_429_TOO_MANY_REQUESTS,
                                detail='The number of attempts has been exhausted. Try again later',
                                headers={'Retry-In': retry_time})
        email_verification.reject_verification(email=user['email'])
    else:
        verification_history = {
            'resend_count': 1,
        }
        cache.add_object(obj_id=cache_id, obj=verification_history, expiration=timedelta(minutes=60))

    verification_code = email_verification.create_verification_code(email=user['email'])
    if verification_code:
        template = TemplateEngine.email_verification_request(recipient_email=user['email'],
                                                             verification_code=verification_code)
        try:
            email_service.send_email(template)
        except:
            raise HTTPException(http_status.HTTP_424_FAILED_DEPENDENCY, 'Try again later')

    return JSONResponse(status_code=http_status.HTTP_200_OK,
                        content={'details': 'Email verification request has been sent'})

