from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portfolio.models import UserProfile, Institute, InstituteRole, FundManager


class Command(BaseCommand):
    help = 'Set up user profile, role, and link to institute'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to set up')
        parser.add_argument('institute_name', type=str, help='Name of the institute')
        parser.add_argument('role', type=str, choices=['admin', 'manager', 'analyst'], help='User role')

    def handle(self, *args, **options):
        username = options['username']
        institute_name = options['institute_name']
        role = options['role']

        try:
            # Get the user
            user = User.objects.get(username=username)
            self.stdout.write(f"Found user: {user.username}")

            # Get or create the institute
            institute, created = Institute.objects.get_or_create(
                name=institute_name,
                defaults={
                    'domain': f"{institute_name.lower()}.com",
                    'subscription_plan': 'basic',
                    'max_users': 50,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created institute: {institute.name}"))
            else:
                self.stdout.write(f"Found institute: {institute.name}")

            # Create or update UserProfile
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'institute': institute,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created UserProfile for {user.username}"))
            else:
                user_profile.institute = institute
                user_profile.is_active = True
                user_profile.save()
                self.stdout.write(self.style.SUCCESS(f"Updated UserProfile for {user.username}"))

            # Create or update InstituteRole
            institute_role, created = InstituteRole.objects.get_or_create(
                user=user,
                institute=institute,
                defaults={'role': role}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created InstituteRole: {role}"))
            else:
                institute_role.role = role
                institute_role.save()
                self.stdout.write(self.style.SUCCESS(f"Updated InstituteRole to: {role}"))

            # If role is manager, create FundManager
            if role == 'manager':
                fund_manager, created = FundManager.objects.get_or_create(
                    user=user,
                    institute=institute,
                    defaults={'is_active': True}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created FundManager for {user.username}"))
                else:
                    fund_manager.is_active = True
                    fund_manager.save()
                    self.stdout.write(self.style.SUCCESS(f"Activated FundManager for {user.username}"))

            self.stdout.write(self.style.SUCCESS(f"\n✓ User {username} is now set up with role '{role}' at {institute.name}"))
            self.stdout.write(f"  They can now login at http://127.0.0.1:8000/")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' not found. Please create the user first in Django admin."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
