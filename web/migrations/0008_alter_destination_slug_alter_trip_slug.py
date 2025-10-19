# Generated manually to make slug fields non-editable in admin
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0007_alter_destination_card_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destination',
            name='slug',
            field=models.SlugField(editable=False, max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='trip',
            name='slug',
            field=models.SlugField(editable=False, max_length=200, unique=True),
        ),
    ]
