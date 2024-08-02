from enum import Enum

from pydantic import BaseModel

from modules.email_service.manager import Senders, Tags


class Templates(Enum):
    app_client_email_verification = 'app_client_email_verification'

    app_client_password_reset_request = 'app_client_password_reset_request'
    app_client_password_reset_completed = 'app_client_password_reset_completed'


class TemplateModel(BaseModel):
    template: Templates
    recipient_email: str
    subject: str
    sender: Senders
    tags: list[Tags]
    open_action_tracking: bool = False
    variables: dict = None


class TemplateEngine:
    @classmethod
    def email_verification_request(cls, recipient_email: str, verification_code: str) -> TemplateModel:
        code_center = len(verification_code) // 2
        first_part_code = verification_code[:code_center]
        second_part_code = verification_code[code_center:]
        return TemplateModel(template=Templates.app_client_email_verification,
                             recipient_email=recipient_email,
                             subject=f'[{first_part_code} {second_part_code}] Email Verification Code',
                             sender=Senders.tech_team,
                             tags=[Tags.email_verification, Tags.action, Tags.tech],
                             variables={
                                 'first_part_code': first_part_code,
                                 'second_part_code': second_part_code
                             })

    @classmethod
    def password_reset_request(cls, recipient_email: str, reset_url: str) -> TemplateModel:
        return TemplateModel(template=Templates.app_client_password_reset_request,
                             recipient_email=recipient_email,
                             subject=f'Password Reset',
                             sender=Senders.tech_team,
                             tags=[Tags.password_reset, Tags.action, Tags.tech],
                             variables={
                                 'reset_url': reset_url
                             })

    @classmethod
    def password_reset_complete(cls, recipient_email: str) -> TemplateModel:
        return TemplateModel(template=Templates.app_client_password_reset_completed,
                             recipient_email=recipient_email,
                             subject=f'Successful Password Reset',
                             sender=Senders.tech_team,
                             tags=[Tags.password_reset, Tags.info, Tags.tech])

