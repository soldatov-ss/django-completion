from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("username", models.CharField(max_length=150, unique=True)),
                ("email", models.EmailField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
