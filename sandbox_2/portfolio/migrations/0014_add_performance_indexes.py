# Generated migration for performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0013_stock_updated_at'),
    ]

    operations = [
        # Add composite index for portfolio lookups by fund_manager and date
        migrations.AddIndex(
            model_name='portfolio',
            index=models.Index(fields=['fund_manager', '-created_at'], name='port_fm_created_idx'),
        ),

        # Add index for stock symbol lookups
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['symbol', 'portfolio'], name='stock_symbol_port_idx'),
        ),

        # Add index for historical data date range queries
        migrations.AddIndex(
            model_name='historicalstockdata',
            index=models.Index(fields=['symbol', 'date'], name='hist_symbol_date_idx'),
        ),

        # Add index for institute active status lookups
        migrations.AddIndex(
            model_name='institute',
            index=models.Index(fields=['is_active', '-created_at'], name='inst_active_created_idx'),
        ),

        # Add index for user profile institute lookups
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['institute', 'is_active'], name='userprof_inst_active_idx'),
        ),
    ]
