# Generated manually on 2025-08-05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('renewals', '0005_caselog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='renewalcase',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('renewed', 'Renewed'),
                    ('cancelled', 'Cancelled'),
                    ('expired', 'Expired'),
                    ('due', 'Due'),
                    ('overdue', 'Overdue'),
                    ('not_required', 'Not Required'),
                    ('assigned', 'Assigned'),
                    ('failed', 'Failed'),
                    ('uploaded', 'Uploaded'),
                ],
                default='pending',
                max_length=20
            ),
        ),
    ]
