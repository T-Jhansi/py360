"""
Management command to set up initial data for the system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Role
from apps.core.models import SystemConfiguration

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial data for the Intelipro Insurance Policy Renewal System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@intelipro.com',
            help='Admin user email address'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='Admin@123',
            help='Admin user password'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up initial data for Intelipro Insurance System...')
        )

        # Create roles
        self.create_roles()
        
        # Create admin user
        self.create_admin_user(options['admin_email'], options['admin_password'])
        
        # Create system configurations
        self.create_system_configurations()
        
        self.stdout.write(
            self.style.SUCCESS('Initial data setup completed successfully!')
        )

    def create_roles(self):
        """Create default user roles"""
        roles_data = [
            {
                'name': 'super_admin',
                'display_name': 'Super Administrator',
                'description': 'Full system access with all permissions',
                'permissions': {
                    'users.view': True,
                    'users.create': True,
                    'users.edit': True,
                    'users.delete': True,
                    'customers.view': True,
                    'customers.create': True,
                    'customers.edit': True,
                    'customers.delete': True,
                    'policies.view': True,
                    'policies.create': True,
                    'policies.edit': True,
                    'policies.delete': True,
                    'campaigns.view': True,
                    'campaigns.create': True,
                    'campaigns.edit': True,
                    'campaigns.delete': True,
                    'analytics.view': True,
                    'system.manage': True,
                }
            },
            {
                'name': 'admin',
                'display_name': 'Administrator',
                'description': 'Administrative access with most permissions',
                'permissions': {
                    'users.view': True,
                    'users.create': True,
                    'users.edit': True,
                    'customers.view': True,
                    'customers.create': True,
                    'customers.edit': True,
                    'customers.delete': True,
                    'policies.view': True,
                    'policies.create': True,
                    'policies.edit': True,
                    'policies.delete': True,
                    'campaigns.view': True,
                    'campaigns.create': True,
                    'campaigns.edit': True,
                    'campaigns.delete': True,
                    'analytics.view': True,
                }
            },
            {
                'name': 'manager',
                'display_name': 'Manager',
                'description': 'Management level access',
                'permissions': {
                    'users.view': True,
                    'customers.view': True,
                    'customers.create': True,
                    'customers.edit': True,
                    'policies.view': True,
                    'policies.create': True,
                    'policies.edit': True,
                    'campaigns.view': True,
                    'campaigns.create': True,
                    'campaigns.edit': True,
                    'analytics.view': True,
                }
            },
            {
                'name': 'agent',
                'display_name': 'Insurance Agent',
                'description': 'Agent level access for customer and policy management',
                'permissions': {
                    'customers.view': True,
                    'customers.create': True,
                    'customers.edit': True,
                    'policies.view': True,
                    'policies.create': True,
                    'policies.edit': True,
                    'campaigns.view': True,
                }
            },
            {
                'name': 'support',
                'display_name': 'Support Staff',
                'description': 'Support level access for customer service',
                'permissions': {
                    'customers.view': True,
                    'customers.edit': True,
                    'policies.view': True,
                    'campaigns.view': True,
                }
            },
            {
                'name': 'viewer',
                'display_name': 'Viewer',
                'description': 'Read-only access to system data',
                'permissions': {
                    'customers.view': True,
                    'policies.view': True,
                    'campaigns.view': True,
                    'analytics.view': True,
                }
            }
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'display_name': role_data['display_name'],
                    'description': role_data['description'],
                    'permissions': role_data['permissions']
                }
            )
            
            if created:
                self.stdout.write(f"Created role: {role.display_name}")
            else:
                self.stdout.write(f"Role already exists: {role.display_name}")

    def create_admin_user(self, email, password):
        """Create admin user"""
        try:
            admin_role = Role.objects.get(name='super_admin')
            
            admin_user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'is_staff': True,
                    'is_superuser': True,
                    'role': admin_role
                }
            )
            
            if created:
                admin_user.set_password(password)
                admin_user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Created admin user: {email}")
                )
            else:
                self.stdout.write(f"Admin user already exists: {email}")
                
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Super admin role not found. Cannot create admin user.")
            )

    def create_system_configurations(self):
        """Create default system configurations"""
        configs = [
            # Email settings
            {
                'category': 'email',
                'key': 'smtp_host',
                'value': 'smtp.gmail.com',
                'description': 'SMTP server hostname'
            },
            {
                'category': 'email',
                'key': 'smtp_port',
                'value': 587,
                'description': 'SMTP server port'
            },
            {
                'category': 'email',
                'key': 'use_tls',
                'value': True,
                'description': 'Use TLS for email encryption'
            },
            
            # File upload settings
            {
                'category': 'uploads',
                'key': 'max_file_size',
                'value': 10485760,  # 10MB
                'description': 'Maximum file upload size in bytes'
            },
            {
                'category': 'uploads',
                'key': 'allowed_extensions',
                'value': ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'],
                'description': 'Allowed file extensions for uploads'
            },
            
            # Security settings
            {
                'category': 'security',
                'key': 'session_timeout',
                'value': 3600,  # 1 hour
                'description': 'Session timeout in seconds'
            },
            {
                'category': 'security',
                'key': 'max_login_attempts',
                'value': 5,
                'description': 'Maximum failed login attempts before account lock'
            },
            {
                'category': 'security',
                'key': 'account_lock_duration',
                'value': 1800,  # 30 minutes
                'description': 'Account lock duration in seconds'
            },
            
            # Business settings
            {
                'category': 'business',
                'key': 'company_name',
                'value': 'Intelipro Insurance',
                'description': 'Company name'
            },
            {
                'category': 'business',
                'key': 'company_address',
                'value': 'Mumbai, India',
                'description': 'Company address'
            },
            {
                'category': 'business',
                'key': 'support_email',
                'value': 'support@intelipro.com',
                'description': 'Support email address'
            },
            {
                'category': 'business',
                'key': 'support_phone',
                'value': '+91-22-12345678',
                'description': 'Support phone number'
            },
            
            # Notification settings
            {
                'category': 'notifications',
                'key': 'renewal_reminder_days',
                'value': [30, 15, 7, 1],
                'description': 'Days before policy expiry to send renewal reminders'
            },
            {
                'category': 'notifications',
                'key': 'email_enabled',
                'value': True,
                'description': 'Enable email notifications'
            },
            {
                'category': 'notifications',
                'key': 'sms_enabled',
                'value': False,
                'description': 'Enable SMS notifications'
            },
        ]

        for config_data in configs:
            config, created = SystemConfiguration.objects.get_or_create(
                category=config_data['category'],
                key=config_data['key'],
                defaults={
                    'value': config_data['value'],
                    'description': config_data['description']
                }
            )
            
            if created:
                self.stdout.write(f"Created config: {config.category}.{config.key}")
            else:
                self.stdout.write(f"Config already exists: {config.category}.{config.key}")

        self.stdout.write(
            self.style.SUCCESS(f"Created {len(configs)} system configurations")
        ) 