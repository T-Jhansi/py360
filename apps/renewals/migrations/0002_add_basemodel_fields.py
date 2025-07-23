# Generated manually to add BaseModel fields to existing renewal_cases table

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('renewals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add BaseModel fields that are missing
        migrations.AddField(
            model_name='renewalcase',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='renewalcase',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='renewalcase',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_renewal_cases', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='renewalcase',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_renewal_cases', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='renewalcase',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_renewal_cases', to=settings.AUTH_USER_MODEL),
        ),
    ]
