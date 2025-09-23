from django.apps import AppConfig


class CustomerPaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customer_payments'
    
    def ready(self):
        """Import signals when the app is ready"""
        import apps.customer_payments.signals
