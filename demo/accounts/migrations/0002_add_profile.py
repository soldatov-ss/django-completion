from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="user",
            name="bio",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
