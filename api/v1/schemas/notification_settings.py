from pydantic import BaseModel


class NotificationSettingsBase(BaseModel):
    '''Base schema for notification settings'''

    mobile_push_notifications: bool
    email_notification_activity_in_workspace: bool
    email_notification_always_send_email_notifications: bool
    email_notification_email_digest: bool
    email_notification_announcement_and_update_emails: bool

    