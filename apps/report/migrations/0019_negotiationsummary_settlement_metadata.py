from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('report', '0018_negotiationsummary_settled_amounts')]

    operations = [
        migrations.AddField(model_name='negotiationsummary', name='settlementVersion', field=models.PositiveIntegerField(default=1)),
        migrations.AddField(model_name='negotiationsummary', name='roundingPolicy', field=models.CharField(default='LARGEST_NOMINAL_HALF_UP_V1', max_length=64)),
        migrations.AddField(model_name='negotiationsummary', name='settlementDimensions', field=models.JSONField(blank=True, null=True)),
    ]
