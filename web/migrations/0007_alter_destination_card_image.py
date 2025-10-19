# Generated manually to switch card_image to ImageField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_remove_destination_cta_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destination',
            name='card_image',
            field=models.ImageField(blank=True, upload_to='destinations/'),
        ),
    ]
