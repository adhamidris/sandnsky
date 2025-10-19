# Generated manually to add additional destinations relation to trips
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0009_trip_card_image_trip_hero_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='additional_destinations',
            field=models.ManyToManyField(blank=True, related_name='additional_trips', to='web.destination'),
        ),
    ]
