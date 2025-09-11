from django.apps import AppConfig


class EmailInboxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.email_inbox'
    verbose_name = 'Email Inbox'
