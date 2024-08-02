import hashlib
import hmac
import json
import os
from enum import Enum

import httpx
from dotenv import load_dotenv

from modules.email_service.manager import MailManager
from modules.email_service.templates import TemplateModel

load_dotenv()

MAILGUN_API_KEY = os.environ['MAILGUN_API_KEY']


class MailGunWebhookStatuses(Enum):
    accepted = 'accepted'
    clicked = 'clicked'
    complained = 'complained'
    delivered = 'delivered'
    opened = 'opened'
    permanent_fail = 'permanent_fail'
    temporary_fail = 'temporary_fail'
    unsubscribed = 'unsubscribed'


class MailGunEndpoints(Enum):
    us = 'https://api.mailgun.net'
    eu = 'https://api.eu.mailgun.net'


class MailGunEngine:
    def __init__(self, api_key: str, marker: str = None):
        self.mail_manager = MailManager()
        self.api_key = api_key
        self.marker = marker

    def __del__(self):
        self.mail_manager.__del__()

    @staticmethod
    def _get_endpoint_base(region: str, domain: str):
        if region == 'us':
            region_endpoint = MailGunEndpoints.us
        elif region == 'eu':
            region_endpoint = MailGunEndpoints.eu
        return f'{region_endpoint.value}/v3/{domain}'

    def _get_auth(self):
        return 'api', self.api_key

    def send_email(self, template: TemplateModel):
        sender = self.mail_manager.get_sender(template.sender)
        domain = sender['domain']
        endpoint = self._get_endpoint_base(region=sender['region'], domain=domain) + '/messages'
        email = f'{sender["email_name"]}@{domain}'

        data = {
            'from': f'{sender["fullname"]} <{email}>',
            'to': template.recipient_email,
            'subject': template.subject,
            'template': template.template.value,
            't:variables': json.dumps(template.variables),
            'o:tag': [tag.value for tag in template.tags],
            'o:tracking-opens': template.open_action_tracking
        }
        response = httpx.post(url=endpoint, auth=self._get_auth(), data=data)
        if response.status_code == 200:
            return response.json()['id'][1:-1]
        raise Exception(f'[{self.marker}] MailGun API Exception [{endpoint}] [{response.status_code}] [{response.text}]')

    @classmethod
    def verify_webhook_signature(cls, signing_key, token, timestamp, signature):
        hmac_digest = hmac.new(key=signing_key.encode(),
                               msg=('{}{}'.format(timestamp, token)).encode(),
                               digestmod=hashlib.sha256).hexdigest()
        return hmac.compare_digest(str(signature), str(hmac_digest))

