from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('email_provider', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailproviderconfig',
            name='access_key_id',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=255,
                help_text='AWS Access Key ID (encrypted)',
            ),
        ),
    ]
