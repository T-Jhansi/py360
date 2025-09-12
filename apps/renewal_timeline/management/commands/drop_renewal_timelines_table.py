from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Drop the renewal_timelines table from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force drop the table without confirmation',
        )

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'renewal_timelines'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.stdout.write(
                    self.style.WARNING('Table renewal_timelines does not exist.')
                )
                return
            
            # Check if table has any data
            cursor.execute("SELECT COUNT(*) FROM renewal_timelines;")
            row_count = cursor.fetchone()[0]
            
            if row_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Table renewal_timelines has {row_count} rows.')
                )
                if not options['force']:
                    confirm = input('Are you sure you want to drop this table? (yes/no): ')
                    if confirm.lower() != 'yes':
                        self.stdout.write('Operation cancelled.')
                        return
            
            # Drop the table
            try:
                cursor.execute("DROP TABLE IF EXISTS renewal_timelines CASCADE;")
                self.stdout.write(
                    self.style.SUCCESS('Successfully dropped renewal_timelines table.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error dropping table: {e}')
                )
