import os
from datetime import timedelta
from enum import Enum
from typing import Annotated

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from modules.api.auxiliary.dependencies import UserManagerDep, PasswordResetVerificationDep, EmailServiceDep
from modules.api.auxiliary.oauth2 import Token, create_access_token, OAuth2
from modules.app.user import UserScope, AccessScopes
from modules.app.verification import VerificationStatus
from modules.email_service.templates import TemplateEngine


load_dotenv()

WEB_APP_ENDPOINT = os.environ['WEB_APP_ENDPOINT']
ACCESS_TOKEN_EXPIRES_IN = 3600

# TODO add auth path
auth_api_router = APIRouter(prefix='', tags=['auth'])


class EmailStatus(Enum):
    available = 'available'
    claimed = 'claimed'
    temporary = 'temporary'


class SignUpStatus(Enum):
    completed = 'completed'
    rejected = 'rejected'


class ResetRequestModel(BaseModel):
    email: str = Field(..., min_length=3, max_length=56)


class ResetPasswordModel(BaseModel):
    secret_token: str
    email: str = Field(..., min_length=3, max_length=56)
    password: str = Field(..., min_length=6, max_length=64)


class SignUpModel(BaseModel):
    fullname: str = Field(..., min_length=2, max_length=32)
    email: str = Field(..., min_length=3, max_length=56)
    password: str = Field(..., min_length=6, max_length=64)


@auth_api_router.post('/token', response_model=Token, summary='OAuth2 Authorization',
                      description='**OAuth2 Authorization. Granting types: "password"')
def get_user_access_token(form_data: Annotated[OAuth2, Depends()],
                          user_manager: UserManagerDep):
    user = None
    scopes = ''

    if form_data.grant_type == 'password':
        if form_data.username and form_data.password:
            status = user_manager.authenticate_user(email=form_data.username, password=form_data.password)
            if status:
                user = user_manager.get_user_by_email(form_data.username)
                scopes = AccessScopes.get_scope_by_role(UserScope.value_to_object(user['user_scope']))

    if not user:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    scopes = [el.value for el in scopes]
    access_token_expires = timedelta(seconds=ACCESS_TOKEN_EXPIRES_IN)
    access_token = create_access_token(data={'sub': str(user['token']), 'scopes': scopes},
                                       expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer', 'expires_in': ACCESS_TOKEN_EXPIRES_IN}


@auth_api_router.post('/signup', summary='Sign Up', description=' ')
def user_sign_up(body: SignUpModel,
                 user_manager: UserManagerDep) -> SignUpStatus:
    status = inspect_email(email=body.email, user_manager=user_manager)
    if status is EmailStatus.claimed:
        return SignUpStatus.rejected
    user_manager.create_new_user(fullname=body.fullname, email=body.email, password=body.password)
    return SignUpStatus.completed


@auth_api_router.get('/email/inspect_email', summary='Email Inspection', description=' ')
def inspect_email(email: str, user_manager: UserManagerDep) -> EmailStatus:
    # TODO Add Request Limit
    if not user_manager.user_email_exists(email):
        return EmailStatus.available
    return EmailStatus.claimed


@auth_api_router.post('/reset_password/request', summary='Password Reset Launcher', description=' ')
def launch_password_reset(body: ResetRequestModel,
                          password_reset_verification: PasswordResetVerificationDep,
                          user_manager: UserManagerDep,
                          email_service: EmailServiceDep):
    # TODO Add Request Limit
    if not user_manager.user_email_exists(body.email):
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, 'Email not found')

    secret_token = password_reset_verification.create_token(body.email)
    if secret_token is VerificationStatus.pending:
        return JSONResponse(status_code=http_status.HTTP_208_ALREADY_REPORTED,
                            content={'details': 'Reset request already sent'})

    reset_url = f'{WEB_APP_ENDPOINT}/client/reset_password?token={secret_token}'
    template = TemplateEngine.password_reset_request(recipient_email=body.email, reset_url=reset_url)
    email_service.send_email(template)
    return JSONResponse(status_code=http_status.HTTP_200_OK, content={'details': 'Reset request has been sent'})


@auth_api_router.post('/reset_password/reset', summary='Password Reset Form', description=' ')
def password_reset(body: ResetPasswordModel,
                   password_reset_verification: PasswordResetVerificationDep,
                   user_manager: UserManagerDep,
                   email_service: EmailServiceDep):
    status, email = password_reset_verification.withdraw_token(body.secret_token)
    if status is VerificationStatus.absent:
        raise HTTPException(http_status.HTTP_401_UNAUTHORIZED, 'Invalid reset request')
    if status is VerificationStatus.withdrawn:
        user_manager.update_user_password(email=email, new_password=body.password)
        template = TemplateEngine.password_reset_complete(recipient_email=email)
        email_service.send_email(template)
        return JSONResponse(status_code=http_status.HTTP_200_OK, content={'details': 'Password has been reset'})
    raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'Something went wrong')

