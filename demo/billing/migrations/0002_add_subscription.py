from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("plan", models.ForeignKey("billing.Plan", on_delete=models.CASCADE)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("active", models.BooleanField(default=True)),
            ],
        ),
    ]
