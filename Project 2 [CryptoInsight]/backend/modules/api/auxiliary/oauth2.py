import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Union

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Form
from fastapi import status as http_status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2PasswordRequestForm
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel, ValidationError

from modules.api.auxiliary.dependencies import UserManagerDep

load_dotenv()

JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
JWT_ALGORITHM = 'HS256'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


class OAuth2(OAuth2PasswordRequestForm):
    def __init__(self,
                 *,
                 grant_type: Annotated[Union[str], Form()],
                 username: Annotated[Union[str, None], Form()] = None,
                 password: Annotated[Union[str, None], Form()] = None,
                 scope: Annotated[str, Form()] = '',
                 client_id: Annotated[Union[str, None], Form()] = None,
                 client_secret: Annotated[Union[str, None], Form()] = None):
        super().__init__(grant_type=grant_type,
                         username=username,
                         password=password,
                         scope=scope,
                         client_id=client_id,
                         client_secret=client_secret)


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    id_token: str | None = None
    scopes: list[str] = []


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def user_auth(security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)],
              user_manager: UserManagerDep):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = 'Bearer'

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        id_token: str = payload.get('sub')
        if id_token is None:
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED,
                                detail='Invalid token',
                                headers={'WWW-Authenticate': authenticate_value})
        token_scopes = payload.get('scopes', [])
        token_data = TokenData(scopes=token_scopes, id_token=id_token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED,
                            detail='Token expired',
                            headers={'WWW-Authenticate': authenticate_value})
    except (JWTError, ValidationError):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED,
                            detail='Unauthorized token',
                            headers={'WWW-Authenticate': authenticate_value})

    user_exists = user_manager.user_token_exists(token_data.id_token)
    if not user_exists:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED,
                            detail='Unauthorized user',
                            headers={'WWW-Authenticate': authenticate_value})

    if not all([scope in token_data.scopes for scope in security_scopes.scopes]):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED,
                            detail='Insufficient permissions',
                            headers={'WWW-Authenticate': authenticate_value})
    return token_data.id_token
