# Generated migration for SaaS schema

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        # Create Organization model
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('domain', models.CharField(blank=True, max_length=200, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription_plan', models.CharField(choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], default='free', max_length=50)),
                ('subscription_status', models.CharField(choices=[('active', 'Active'), ('trialing', 'Trialing'), ('past_due', 'Past Due'), ('canceled', 'Canceled'), ('unpaid', 'Unpaid')], default='trialing', max_length=50)),
                ('trial_ends_at', models.DateTimeField(blank=True, null=True)),
                ('max_fund_managers', models.IntegerField(default=1)),
                ('max_clients', models.IntegerField(default=5)),
                ('max_portfolios', models.IntegerField(default=10)),
                ('billing_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('support_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Organization (Tenant)',
                'verbose_name_plural': 'Organizations (Tenants)',
                'ordering': ['name'],
            },
        ),
        
        # Create OrganizationAdmin model
        migrations.CreateModel(
            name='OrganizationAdmin',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('is_primary_admin', models.BooleanField(default=False)),
                ('can_manage_billing', models.BooleanField(default=True)),
                ('can_manage_users', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.organization')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='organizationadmin', to='auth.user')),
            ],
            options={
                'verbose_name': 'Organization Admin',
                'verbose_name_plural': 'Organization Admins',
                'ordering': ['organization__name', 'user__username'],
            },
        ),
        
        # Create FundManager model
        migrations.CreateModel(
            name='FundManager',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('license_number', models.CharField(max_length=100)),
                ('company_name', models.CharField(blank=True, max_length=200, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.organization')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fundmanager', to='auth.user')),
            ],
            options={
                'verbose_name': 'Fund Manager',
                'verbose_name_plural': 'Fund Managers',
                'ordering': ['organization__name', 'user__username'],
            },
        ),
        
        # Create Client model
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('client_id', models.CharField(max_length=50, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('risk_tolerance', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=50)),
                ('investment_goals', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fund_manager', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.fundmanager')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.organization')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='client', to='auth.user')),
            ],
            options={
                'verbose_name': 'Client',
                'verbose_name_plural': 'Clients',
                'ordering': ['organization__name', 'fund_manager__user__username', 'last_name'],
            },
        ),
        
        # Create Portfolio model
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_public', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.client')),
                ('fund_manager', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.fundmanager')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.organization')),
            ],
            options={
                'verbose_name': 'Portfolio',
                'verbose_name_plural': 'Portfolios',
                'ordering': ['organization__name', 'client__last_name', 'name'],
            },
        ),
        
        # Create Stock model
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('symbol', models.CharField(max_length=10)),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('quantity', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=4, max_digits=10)),
                ('last_price_update', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.organization')),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.portfolio')),
            ],
            options={
                'verbose_name': 'Stock',
                'verbose_name_plural': 'Stocks',
                'ordering': ['portfolio__name', 'symbol'],
            },
        ),
        
        # Create Subscription model
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('plan', models.CharField(choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], default='free', max_length=50)),
                ('status', models.CharField(choices=[('active', 'Active'), ('trialing', 'Trialing'), ('past_due', 'Past Due'), ('canceled', 'Canceled'), ('unpaid', 'Unpaid')], default='trialing', max_length=50)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('trial_ends_at', models.DateTimeField(blank=True, null=True)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=255, null=True)),
                ('stripe_price_id', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='portfolio.organization')),
            ],
            options={
                'verbose_name': 'Subscription',
                'verbose_name_plural': 'Subscriptions',
                'ordering': ['organization__name'],
            },
        ),
    ]
