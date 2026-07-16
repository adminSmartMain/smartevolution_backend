from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0012_administration_portal_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo',
            field=models.URLField(blank=True, max_length=1024, null=True),
        ),
    ]
