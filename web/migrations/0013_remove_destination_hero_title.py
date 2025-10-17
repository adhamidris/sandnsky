from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0012_destination_hero_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='destination',
            name='hero_title',
        ),
    ]
