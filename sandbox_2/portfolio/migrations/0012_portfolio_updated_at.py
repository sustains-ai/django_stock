# Generated migration to add updated_at to Portfolio

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0011_auto_20251002_1109'),
    ]

    operations = [
        # Add updated_at to Portfolio
        migrations.AddField(
            model_name='portfolio',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
