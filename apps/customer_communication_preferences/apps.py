from django.apps import AppConfig


class CustomerCommunicationPreferencesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customer_communication_preferences'
    
    def ready(self):
        """Import signals when the app is ready"""
        import apps.customer_communication_preferences.signals
