from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User, Role


class Command(BaseCommand):
    help = 'Assign default roles to users who do not have roles assigned'

    def add_arguments(self, parser):
        parser.add_argument(
            '--default-role',
            type=str,
            default='agent',
            help='Default role name to assign (default: agent)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        default_role_name = options['default_role']
        dry_run = options['dry_run']

        try:
            # Get the default role
            try:
                default_role = Role.objects.get(name=default_role_name)
                self.stdout.write(
                    self.style.SUCCESS(f'Found default role: {default_role.display_name} ({default_role.name})')
                )
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Role "{default_role_name}" not found. Available roles:')
                )
                roles = Role.objects.all()
                for role in roles:
                    self.stdout.write(f'  - {role.name} ({role.display_name})')
                return

            # Find users without roles
            users_without_roles = User.objects.filter(role__isnull=True, is_active=True)
            count = users_without_roles.count()

            if count == 0:
                self.stdout.write(
                    self.style.SUCCESS('All active users already have roles assigned.')
                )
                return

            self.stdout.write(
                self.style.WARNING(f'Found {count} users without roles:')
            )

            for user in users_without_roles:
                self.stdout.write(f'  - {user.email} ({user.full_name})')

            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN: No changes will be made.')
                )
                return

            # Confirm action
            confirm = input(f'\nAssign role "{default_role.display_name}" to {count} users? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return

            # Assign roles
            with transaction.atomic():
                updated_count = users_without_roles.update(role=default_role)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully assigned role "{default_role.display_name}" to {updated_count} users.'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
