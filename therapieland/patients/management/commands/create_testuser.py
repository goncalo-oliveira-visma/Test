from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a test user'

    def handle(self, *args, **options):
        if User.objects.filter(username='testuser').exists():
            self.stdout.write(self.style.WARNING('User "testuser" already exists'))
            return

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created user: {user.username}')
        )