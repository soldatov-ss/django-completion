from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="post",
            name="slug",
            field=models.SlugField(blank=True, max_length=200),
        ),
    ]
