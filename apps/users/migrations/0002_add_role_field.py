# Generated migration to add role field to UserProfile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                choices=[('farmer', 'Farmer'), ('admin', 'Admin'), ('operator', 'Operator')],
                default='farmer',
                max_length=20
            ),
        ),
    ]
