# Generated manually to add trip image uploads
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0008_alter_destination_slug_alter_trip_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='card_image',
            field=models.ImageField(blank=True, upload_to='trips/cards/'),
        ),
        migrations.AddField(
            model_name='trip',
            name='hero_image',
            field=models.ImageField(blank=True, upload_to='trips/hero/'),
        ),
    ]
