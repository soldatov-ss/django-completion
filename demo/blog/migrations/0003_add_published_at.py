from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0002_add_slug")]
    operations = [
        migrations.AddField(
            model_name="post",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
