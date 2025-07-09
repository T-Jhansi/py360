"""
Celery configuration for Intelipro Insurance Policy Renewal System.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'renewal_backend.settings.development')

app = Celery('renewal_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Process pending campaigns every 5 minutes
    'process-pending-campaigns': {
        'task': 'apps.campaigns.tasks.process_pending_campaigns',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Sync email accounts every 10 minutes
    'sync-email-accounts': {
        'task': 'apps.emails.tasks.sync_all_email_accounts',
        'schedule': 600.0,  # 10 minutes
    },
    
    # Update campaign metrics every 15 minutes
    'update-campaign-metrics': {
        'task': 'apps.campaigns.tasks.update_campaign_metrics',
        'schedule': 900.0,  # 15 minutes
    },
    
    # Process renewal reminders daily at 9 AM
    'process-renewal-reminders': {
        'task': 'apps.policies.tasks.process_renewal_reminders',
        'schedule': 86400.0,  # 24 hours
        'options': {'expires': 3600}  # Expire after 1 hour
    },
    
    # Clean up old files weekly
    'cleanup-old-files': {
        'task': 'apps.files.tasks.cleanup_old_files',
        'schedule': 604800.0,  # 7 days
    },
    
    # Generate analytics reports daily
    'generate-daily-analytics': {
        'task': 'apps.analytics.tasks.generate_daily_reports',
        'schedule': 86400.0,  # 24 hours
    },
}

# Celery task routes
app.conf.task_routes = {
    'apps.campaigns.tasks.*': {'queue': 'campaigns'},
    'apps.emails.tasks.*': {'queue': 'emails'},
    'apps.communications.tasks.*': {'queue': 'communications'},
    'apps.uploads.tasks.*': {'queue': 'uploads'},
    'apps.analytics.tasks.*': {'queue': 'analytics'},
}

# Error handling
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Task failure handling
@app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """Handle task failures"""
    from apps.notifications.models import Notification
    from apps.users.models import User
    
    # Notify administrators about task failures
    admin_users = User.objects.filter(is_superuser=True)
    for admin in admin_users:
        Notification.objects.create(
            user=admin,
            type='task_failure',
            title='Background Task Failed',
            message=f'Task {task_id} failed with error: {error}',
            data={'task_id': task_id, 'error': str(error), 'traceback': traceback}
        )

# Custom task configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
) 