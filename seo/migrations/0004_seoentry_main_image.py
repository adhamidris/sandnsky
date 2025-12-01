from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0003_rename_seo_seoentr_page_ty_b61dd1_idx_seo_seoentr_page_ty_9ceb47_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="seoentry",
            name="main_image",
            field=models.ImageField(
                blank=True,
                help_text="Primary image override for this page.",
                max_length=255,
                null=True,
                upload_to="seo/images/",
            ),
        ),
    ]
