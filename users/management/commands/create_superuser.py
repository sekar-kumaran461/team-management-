"""
Management command to create a superuser from environment variables
Usage: python manage.py create_superuser
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser from environment variables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='sekarkumaran547@gmail.com',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='sekarvifadmin',
        )

    def handle(self, *args, **options):
        # Get superuser credentials from environment or arguments
        email = options.get('email') or os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = options.get('password') or os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not email or not password:
            self.stdout.write(
                self.style.ERROR(
                    'Superuser email and password must be provided via arguments or environment variables:\n'
                    'DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD'
                )
            )
            return

        try:
            # Check if superuser already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Superuser with email {email} already exists')
                )
                return

            # Create superuser
            user = User.objects.create_superuser(
                email=email,
                password=password,
                username=email.split('@')[0],  # Use email prefix as username
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {email}')
            )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
