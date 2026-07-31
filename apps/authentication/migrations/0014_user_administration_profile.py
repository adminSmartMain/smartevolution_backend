from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0013_user_profile_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='organization',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='archived_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='token_version',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
