from fastapi import BackgroundTasks, Request, requests

from api.v1.models.contact_us import ContactUs
from api.v1.models.user import User
from api.core.dependencies.email.email_sender import send_email


SUPPORT_LINK = 'https://smashtravels.com/contact-us'
UNSUBSCRIBE_LINK = 'https://smashtravels.com/unsubscribe'


class EmailSendingService:
    """
    This service just allows for sending different types of email messages
    """

    def send_welcome_email(self, request: Request, background_tasks: BackgroundTasks, user: User):
        '''This function sends the welcome email to a user'''

        background_tasks.add_task(
            send_email,
            recipient=user.email,
            template_name="welcome.html",
            subject=f"🎉 Welcome, {user.first_name}! Start Your Journey with SmashTravels",
            context={
                "request": request,
                "user": user,
                "cta_link": "https://smashtravels.com/about-us",
                "unsubscribe_link": UNSUBSCRIBE_LINK
            }
        )
     
    


    def send_reset_password_email(self, request: Request, background_tasks: BackgroundTasks, user: User, reset_url: str):
        '''This function sends the reset password email to a user'''

        background_tasks.add_task(
            send_email,
            recipient=user.email,
            template_name="reset-password.html",
            subject="Reset Password",
            context={
                "request": request,
                "user": user,
                "url": reset_url
            }
        )
    

    def send_reset_password_success_email(self, request: Request, background_tasks: BackgroundTasks, user: User):
        '''This function sends the reset password success email to a user'''

        background_tasks.add_task(
            send_email,
            recipient=user.email,
            template_name="password-reset-complete.html",
            subject="Password Reset Complete",
            context={
                "request": request,
                "user": user,
            }
        )
    

    def send_contact_us_success_email(self, request: Request, background_tasks: BackgroundTasks, contact_message: ContactUs):
        '''This function sends a contact us success email to the specified email'''

        background_tasks.add_task(
            send_email,
            recipient=contact_message.email,
            template_name="contact-us-success.html",
            subject="Contact us message sent successfully",
            context={
                "request": request,
                "message": contact_message,
            }
        )


email_sending_service = EmailSendingService()
