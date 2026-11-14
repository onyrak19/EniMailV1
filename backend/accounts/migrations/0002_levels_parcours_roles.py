from django.db import migrations, models


def seed(apps, schema_editor):
    Level, Parcours, Role = apps.get_model("accounts", "Level"), apps.get_model("accounts", "Parcours"), apps.get_model("accounts", "Role")
    for i, c in enumerate(["L1", "L2", "L3", "M1", "M2"], 1):
        Level.objects.get_or_create(code=c, defaults={"name": c, "order": i})
    for i, c in enumerate(["IG", "GB", "ASR", "MDI"], 1):
        Parcours.objects.get_or_create(code=c, defaults={"name": c, "order": i})
    roles = [
        ("admin", "Administrateur", dict(can_broadcast=True)),
        ("teacher", "Professeur", dict(requires_approval=True, can_broadcast=True, self_register=True)),
        ("student", "\u00c9tudiant", dict(has_academic=True, self_register=True)),
    ]
    for code, name, flags in roles:
        Role.objects.get_or_create(code=code, defaults=dict(name=name, is_system=True, **flags))


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Level",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(blank=True, max_length=60)),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["order", "code"]},
        ),
        migrations.CreateModel(
            name="Parcours",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(blank=True, max_length=60)),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["order", "code"], "verbose_name_plural": "parcours"},
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=30, unique=True)),
                ("name", models.CharField(max_length=60)),
                ("is_system", models.BooleanField(default=False)),
                ("has_academic", models.BooleanField(default=False)),
                ("requires_approval", models.BooleanField(default=False)),
                ("can_broadcast", models.BooleanField(default=False)),
                ("self_register", models.BooleanField(default=False)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AlterField(model_name="user", name="role", field=models.CharField(default="student", max_length=30)),
        migrations.AlterField(model_name="user", name="level", field=models.CharField(blank=True, max_length=20)),
        migrations.AlterField(model_name="user", name="parcours", field=models.CharField(blank=True, max_length=20)),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
