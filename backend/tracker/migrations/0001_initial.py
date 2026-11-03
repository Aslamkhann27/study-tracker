import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Subject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subjects", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [models.UniqueConstraint(fields=("user", "name"), name="unique_subject_per_user")],
            },
        ),
        migrations.CreateModel(
            name="StudyEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("study_date", models.DateField()),
                ("target_hours", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("actual_hours", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("notes", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="entries", to="tracker.subject")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="study_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-study_date", "subject__name"],
                "constraints": [models.UniqueConstraint(fields=("user", "subject", "study_date"), name="unique_daily_subject_entry")],
                "indexes": [models.Index(fields=["user", "study_date"], name="tracker_st_user_i_6d95d1_idx")],
            },
        ),
    ]
