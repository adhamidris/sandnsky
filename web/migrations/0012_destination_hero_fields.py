from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0011_update_destination_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='destination',
            name='hero_image',
            field=models.ImageField(blank=True, upload_to='destinations/hero/'),
        ),
        migrations.AddField(
            model_name='destination',
            name='hero_subtitle',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='destination',
            name='hero_title',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
