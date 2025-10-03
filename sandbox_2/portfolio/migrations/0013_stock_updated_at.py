# Generated migration to add updated_at to Stock

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0012_portfolio_updated_at'),
    ]

    operations = [
        # Add updated_at to Stock
        migrations.AddField(
            model_name='stock',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
