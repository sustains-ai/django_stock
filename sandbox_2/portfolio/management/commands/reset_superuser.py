from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
import getpass
import sys


class Command(BaseCommand):
    help = 'Delete all existing superusers and create a new one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the new superuser',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the new superuser',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the new superuser (not recommended for production)',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Skip interactive prompts (requires --username, --email, --password)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt for deleting existing superusers',
        )

    def handle(self, *args, **options):
        # Get current superusers
        existing_superusers = User.objects.filter(is_superuser=True)
        
        if existing_superusers.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Found {existing_superusers.count()} existing superuser(s):'
                )
            )
            for user in existing_superusers:
                self.stdout.write(f'  - {user.username} ({user.email})')
            
            if not options['force']:
                confirm = input('\nAre you sure you want to delete all existing superusers? (yes/no): ')
                if confirm.lower() not in ['yes', 'y']:
                    self.stdout.write(self.style.ERROR('Operation cancelled.'))
                    return
        
        # Delete existing superusers
        with transaction.atomic():
            deleted_count = existing_superusers.count()
            existing_superusers.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} existing superuser(s).')
            )
        
        # Create new superuser
        if options['noinput']:
            if not all([options['username'], options['email'], options['password']]):
                raise CommandError(
                    '--noinput requires --username, --email, and --password to be provided.'
                )
            username = options['username']
            email = options['email']
            password = options['password']
        else:
            # Interactive mode
            self.stdout.write('\nCreating new superuser:')
            
            # Get username
            if options['username']:
                username = options['username']
            else:
                username = input('Username: ')
                if not username:
                    raise CommandError('Username cannot be empty.')
            
            # Get email
            if options['email']:
                email = options['email']
            else:
                email = input('Email address: ')
                if not email:
                    raise CommandError('Email cannot be empty.')
            
            # Get password
            if options['password']:
                password = options['password']
            else:
                password = getpass.getpass('Password: ')
                if not password:
                    raise CommandError('Password cannot be empty.')
                
                password_confirm = getpass.getpass('Password (again): ')
                if password != password_confirm:
                    raise CommandError('Passwords do not match.')
        
        # Create the new superuser
        try:
            with transaction.atomic():
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    raise CommandError(f'Username "{username}" already exists.')
                
                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    raise CommandError(f'Email "{email}" already exists.')
                
                # Create the superuser
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created new superuser: {username} ({email})'
                    )
                )
                
        except ValidationError as e:
            raise CommandError(f'Validation error: {e}')
        except Exception as e:
            raise CommandError(f'Error creating superuser: {e}')
        
        # Display final status
        total_superusers = User.objects.filter(is_superuser=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Total superusers in database: {total_superusers}'
            )
        )
