import os
from datetime import timedelta
from enum import Enum

import uuid6
from dotenv import load_dotenv
from passlib.context import CryptContext

from modules.db.engine import MongoEngine, MongoKeys
from modules.tools import CacheStorage

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']


class UserScope(Enum):
    admin = 'admin'
    regular = 'regular'
    premium = 'premium'
    unverified = 'unverified'

    @classmethod
    def value_to_object(cls, value: str):
        for role in cls:
            if role.value == value:
                return role
        return None


class AccessScopes(Enum):
    access_tier_0 = 'AT0'   # unverified
    access_tier_1 = 'AT1'   # regular
    access_tier_2 = 'AT2'   # premium

    @classmethod
    def get_scope_by_role(cls, role: UserScope):
        if role is UserScope.admin:
            return [el for el in cls]
        if role is UserScope.regular:
            return [cls.access_tier_1]
        if role is UserScope.premium:
            return [cls.access_tier_1]
        if role is UserScope.unverified:
            return [cls.access_tier_0]
        return []


class UserManager:
    def __init__(self, marker: str):
        self.mongo_db = MongoEngine(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PASSWORD,
                                    marker=f'user_manager_{marker}')
        self.pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        self.__user_cache = CacheStorage()

    def __del__(self):
        self.mongo_db.__del__()
        self.__user_cache.__del__()

    def get_user_by_token(self, user_token: str):
        user = self.__user_cache.get_object(user_token)
        if not user:
            user = self.mongo_db.find_one(db=MongoKeys.app_db, key=MongoKeys.app_users, target={'token': user_token})
            if user:
                self.__user_cache.add_object(obj_id=user_token, obj=user, expiration=timedelta(minutes=30))
                self.__user_cache.add_index(obj_id=user_token, alter_id=user['email'])
        return user

    def get_user_by_email(self, email: str):
        user = self.__user_cache.get_object(email)
        if not user:
            user_token = self.mongo_db.find_one(db=MongoKeys.app_db, key=MongoKeys.app_users, target={'email': email},
                                                project={'token': 1, '_id': 0})
            if user_token:
                user = self.get_user_by_token(user_token['token'])
        return user

    def authenticate_user(self, email: str, password: str):
        user = self.get_user_by_email(email)
        if not user or not self.pwd_context.verify(self.get_password_line(email, password), user['password_hash']):
            return False
        return True

    def user_token_exists(self, user_token: str):
        return self.mongo_db.exists(db=MongoKeys.app_db, key=MongoKeys.app_users, target={'token': user_token})

    def user_email_exists(self, email: str):
        return self.mongo_db.exists(db=MongoKeys.app_db, key=MongoKeys.app_users, target={'email': email})

    def create_new_user(self, fullname: str, email: str, password: str):
        if self.user_email_exists(email):
            raise Exception('The user with the e-mail already exists')

        password_hash = self.pwd_context.hash(self.get_password_line(email, password))
        token = uuid6.uuid7().hex
        new_user = {
            'token': uuid6.uuid7().hex,
            'fullname': fullname,
            'email': email,
            'password_hash': password_hash,
            'user_scope': UserScope.unverified.value
        }

        self.mongo_db.insert(db=MongoKeys.app_db, key=MongoKeys.app_users, data=new_user)
        self.get_user_by_token(token)
        return token

    def update_user_scope(self, user_token: str, scope: UserScope):
        self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_users,
                                 target={'token': user_token},
                                 update_query={'$set': {'user_scope': scope.value}})
        user = self.get_user_by_token(user_token)
        user['user_scope'] = scope.value

    def get_user_scopes(self, user_token: str):
        user = self.get_user_by_token(user_token)
        return AccessScopes.get_scope_by_role(UserScope.value_to_object(user['user_scope']))

    def update_user_password(self, email: str, new_password):
        password_hash = self.pwd_context.hash(self.get_password_line(email, new_password))
        self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_users,
                                 target={'email': email},
                                 update_query={'$set': {'password_hash': password_hash}})
        user = self.get_user_by_email(email)
        user['password_hash'] = password_hash

    @staticmethod
    def get_password_line(email: str, password: str):
        return f':crypto_insight:{email}:{password}:'

