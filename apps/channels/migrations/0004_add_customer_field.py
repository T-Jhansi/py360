# Generated manually for adding customer field to Channel model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
        ('business_channels', '0003_change_manager_to_text_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='customer',
            field=models.ForeignKey(
                blank=True,
                help_text='Customer associated with this channel',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='channels',
                to='customers.customer'
            ),
        ),
        migrations.AddIndex(
            model_name='channel',
            index=models.Index(fields=['customer'], name='channel_customer_idx'),
        ),
    ]
