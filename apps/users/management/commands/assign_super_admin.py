from django.core.management.base import BaseCommand
from apps.users.models import User, Role


class Command(BaseCommand):
    help = 'Assign super_admin role to a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email of the user to assign super_admin role'
        )

    def handle(self, *args, **options):
        email = options['email']

        try:
            # Get the user
            try:
                user = User.objects.get(email=email)
                self.stdout.write(f'Found user: {user.email} ({user.full_name})')
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email "{email}" not found.')
                )
                return

            # Get the super_admin role
            try:
                super_admin_role = Role.objects.get(name='super_admin')
                self.stdout.write(f'Found role: {super_admin_role.display_name} ({super_admin_role.name})')
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('super_admin role not found. Available roles:')
                )
                roles = Role.objects.all()
                for role in roles:
                    self.stdout.write(f'  - {role.name} ({role.display_name})')
                return

            # Check current role
            if user.role:
                self.stdout.write(f'Current role: {user.role.display_name} ({user.role.name})')
            else:
                self.stdout.write('Current role: None')

            # Assign super_admin role
            user.role = super_admin_role
            user.save(update_fields=['role'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully assigned super_admin role to {user.email}'
                )
            )

            # Show permissions
            permissions = user.get_permissions()
            if isinstance(permissions, list):
                self.stdout.write(f'User permissions: {permissions}')
            else:
                self.stdout.write(f'User permissions: {list(permissions.keys()) if permissions else []}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
