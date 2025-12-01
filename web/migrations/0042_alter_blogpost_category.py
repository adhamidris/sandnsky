from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0041_alter_bookingconfirmationemailsettings_body_text_template"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogpost",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="posts",
                to="web.blogcategory",
            ),
        ),
    ]
