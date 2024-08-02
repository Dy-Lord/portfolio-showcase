import os
import secrets
import string
from datetime import timedelta, datetime, timezone
from enum import Enum

from dotenv import load_dotenv

from modules.db.engine import MongoEngine, MongoKeys
from modules.tools import CronThread, try_extract

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']


class VerificationStatus(Enum):
    verified = 'verified'
    pending = 'pending'
    blocked = 'blocked'
    expired = 'expired'
    rejected = 'rejected'
    invalid_code = 'invalid_code'
    withdrawn = 'withdrawn'
    absent = 'absent'


class EmailVerification:
    def __init__(self, code_length: int = 6, code_expiration: timedelta = timedelta(hours=1),
                 attempt_limit: int = 10, marker: str = None):
        self.code_length = code_length
        self.code_expiration = code_expiration
        self.attempt_limit = attempt_limit
        self.marker = marker
        self.mongo_db = MongoEngine(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PASSWORD,
                                    marker='EmailVerification')
        self.jobs: dict[str, list[CronThread, int]] = {}
        self._launch()

    def __del__(self):
        for job_id in list(self.jobs.keys()):
            self._terminate_job(job_id)
        self.mongo_db.__del__()

    def _launch(self):
        active_jobs = self.mongo_db.find(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                         target={'status': VerificationStatus.pending.value})
        for job in active_jobs:
            expires_at = job['expires_at'].replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                self._verification_expired(job['_id'])
            else:
                verification_job = CronThread(start_time=expires_at,
                                              target=lambda: self._verification_expired(job['_id']),
                                              call_limit=1, marker=f'email_verification_{job["_id"]}')
                self.jobs.update({job['_id']: [verification_job, job['attempts']]})

    def _terminate_job(self, job_id):
        job = try_extract(lambda: self.jobs.pop(job_id))
        if job:
            job[0].terminate()
            self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                     target={'_id': job_id},
                                     update_query={'$set': {'attempts': job[1]}})

    def _verification_expired(self, job_id):
        self._terminate_job(job_id)
        self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                 target={'_id': job_id}, update_query={'$set': {'status': VerificationStatus.expired.value}})

    def _block_verification(self, job_id):
        self._terminate_job(job_id)
        self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                 target={'_id': job_id},
                                 update_query={'$set': {'status': VerificationStatus.blocked.value}})

    def reject_verification(self, email: str):
        active_verification = self.mongo_db.find_one(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                                     target={'email': email, 'status': VerificationStatus.pending.value})
        if not active_verification:
            return VerificationStatus.expired

        job_id = active_verification['_id']
        self._terminate_job(job_id)
        self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                 target={'_id': job_id}, update_query={'$set': {'status': VerificationStatus.rejected.value}})

    def verify_code(self, secret_code: str, email: str):
        active_verification = self.mongo_db.find_one(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                                     target={'email': email, 'status': VerificationStatus.pending.value})
        if not active_verification:
            return VerificationStatus.absent

        job_id = active_verification['_id']
        self.jobs[job_id][1] += 1
        if self.jobs[job_id][1] > self.attempt_limit:
            self._block_verification(job_id)
            return VerificationStatus.blocked

        if secrets.compare_digest(secret_code, active_verification['code']):
            self._terminate_job(job_id)
            self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                     target={'_id': job_id}, update_query={'$set': {'status': VerificationStatus.verified.value}})
            return VerificationStatus.verified
        return VerificationStatus.invalid_code

    def create_verification_code(self, email: str):
        if self.mongo_db.exists(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                target={'email': email, 'status': VerificationStatus.pending.value}):
            return None
        secret_code = ''.join(secrets.choice(string.digits) for _ in range(self.code_length))
        expires_at = datetime.now(timezone.utc) + self.code_expiration
        new_verification = {
            'code': secret_code,
            'email': email,
            'requested_at': datetime.now(timezone.utc),
            'expires_at': expires_at,
            'attempts': 0,
            'status': VerificationStatus.pending.value
        }

        job_id = self.mongo_db.insert(db=MongoKeys.app_db, key=MongoKeys.app_email_verification,
                                      data=new_verification).inserted_id

        verification_job = CronThread(start_time=expires_at, target=lambda: self._verification_expired(job_id),
                                      call_limit=1, marker=f'email_verification_{job_id}')
        self.jobs.update({job_id: [verification_job, 0]})
        return secret_code


class PasswordResetVerification:
    def __init__(self, token_expiration: timedelta = timedelta(hours=1), marker: str = None):
        self.token_expiration = token_expiration
        self.marker = marker
        self.mongo_db = MongoEngine(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PASSWORD,
                                    marker='PasswordResetVerification')
        self.jobs: dict[str, CronThread] = {}

    def __del__(self):
        for job_id in list(self.jobs.keys()):
            self._terminate_job(job_id)
        self.mongo_db.__del__()

    def _terminate_job(self, job_id):
        try_extract(lambda: self.jobs.pop(job_id).terminate())

    def _verification_expired(self, job_id):
        self._terminate_job(job_id)
        self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_password_reset_verification,
                                 target={'_id': job_id},
                                 update_query={'$set': {'status': VerificationStatus.expired.value}})

    def withdraw_token(self, secret_token: str):
        active_verification = self.mongo_db.find_one(db=MongoKeys.app_db, key=MongoKeys.app_password_reset_verification,
                                                     target={'secret_token': secret_token,
                                                             'status': VerificationStatus.pending.value})
        if not active_verification:
            return VerificationStatus.absent, None

        self._terminate_job(active_verification['_id'])
        self.mongo_db.update_one(db=MongoKeys.app_db, key=MongoKeys.app_password_reset_verification,
                                 target={'secret_token': secret_token},
                                 update_query={'$set': {'status': VerificationStatus.withdrawn.value}})
        return VerificationStatus.withdrawn, active_verification['email']

    def create_token(self, email: str):
        if self.mongo_db.find_one(db=MongoKeys.app_db, key=MongoKeys.app_password_reset_verification,
                                  target={'email': email, 'status': VerificationStatus.pending.value}):
            return VerificationStatus.pending

        secret_token = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + self.token_expiration
        new_verification = {
            'secret_token': secret_token,
            'email': email,
            'requested_at': datetime.now(timezone.utc),
            'expires_at': expires_at,
            'status': VerificationStatus.pending.value
        }

        job_id = self.mongo_db.insert(db=MongoKeys.app_db, key=MongoKeys.app_password_reset_verification,
                                      data=new_verification).inserted_id

        verification_job = CronThread(start_time=expires_at, target=lambda: self._verification_expired(job_id),
                                      call_limit=1, marker=f'password_reset_{job_id}')
        self.jobs.update({job_id: [verification_job, 0]})
        return secret_token

