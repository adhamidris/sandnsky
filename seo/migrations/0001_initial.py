from django.db import migrations, models
import django.db.models.deletion
import django.contrib.contenttypes.models
import django.contrib.contenttypes.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="SeoEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("page_type", models.CharField(choices=[("trip", "Trip"), ("destination", "Destination"), ("blog_post", "Blog post"), ("static", "Static page")], db_index=True, max_length=50)),
                ("object_id", models.PositiveIntegerField(blank=True, db_index=True, null=True)),
                ("page_code", models.CharField(blank=True, db_index=True, help_text="Identifier for static pages (e.g., home, trips_list).", max_length=100)),
                ("slug", models.SlugField(blank=True, max_length=200)),
                ("path", models.CharField(help_text="Absolute path for the page (e.g., /trips/my-trip/).", max_length=500, unique=True)),
                ("meta_title", models.CharField(blank=True, max_length=255)),
                ("meta_description", models.CharField(blank=True, max_length=320)),
                ("meta_keywords", models.CharField(blank=True, max_length=500)),
                ("alt_text", models.CharField(blank=True, help_text="Alt text for the main hero/primary image on the page.", max_length=255)),
                ("canonical_url", models.CharField(blank=True, help_text="Canonical URL. Leave blank to default to self.", max_length=500)),
                ("body_override", models.TextField(blank=True, help_text="Optional SEO-focused body copy override (English-only).")),
                ("is_indexable", models.BooleanField(default=True, help_text="Whether the page should be indexed (English-only).")),
                ("status_flags", models.JSONField(blank=True, default=dict, help_text="Lightweight flags (e.g., missing_meta, missing_alt).")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "content_type",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="seo_entries", to="contenttypes.contenttype"),
                ),
            ],
            options={
                "ordering": ["page_type", "path"],
            },
        ),
        migrations.CreateModel(
            name="SeoRedirect",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("from_path", models.CharField(help_text="Source path to redirect from (absolute, no domain).", max_length=500, unique=True)),
                ("to_path", models.CharField(help_text="Destination path (absolute, no domain).", max_length=500)),
                ("is_permanent", models.BooleanField(default=True, help_text="True for 301, False for 302.")),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "entry",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="redirects", to="seo.seoentry"),
                ),
            ],
            options={
                "ordering": ["from_path"],
                "verbose_name": "SEO redirect",
                "verbose_name_plural": "SEO redirects",
            },
        ),
        migrations.CreateModel(
            name="SeoSnippet",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("name", models.CharField(max_length=150)),
                ("placement", models.CharField(choices=[("head", "Head"), ("body", "Body")], default="head", max_length=10)),
                ("value", models.TextField(help_text="Raw HTML/script for injection. Restrict to trusted admins.")),
                ("is_active", models.BooleanField(default=True)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "entry",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="snippets", to="seo.seoentry"),
                ),
            ],
            options={
                "ordering": ["entry", "placement", "position", "id"],
                "verbose_name": "SEO snippet",
                "verbose_name_plural": "SEO snippets",
            },
        ),
        migrations.CreateModel(
            name="SeoFaq",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("question", models.CharField(max_length=300)),
                ("answer", models.TextField(blank=True)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "entry",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="faqs", to="seo.seoentry"),
                ),
            ],
            options={
                "ordering": ["entry", "position", "id"],
                "verbose_name": "SEO FAQ",
                "verbose_name_plural": "SEO FAQs",
            },
        ),
        migrations.AddIndex(
            model_name="seoentry",
            index=models.Index(fields=["page_type", "path"], name="seo_seoentr_page_ty_b61dd1_idx"),
        ),
        migrations.AddIndex(
            model_name="seoentry",
            index=models.Index(fields=["page_type", "page_code"], name="seo_seoentr_page_ty_1d98f4_idx"),
        ),
    ]
