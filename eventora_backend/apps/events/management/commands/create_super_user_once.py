from django.core.management.base import BaseCommand
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Create a superuser for first-time setup'

    def handle(self, *args, **kwargs):
        email = 'admin@eventora.com'
        password = 'Admin1234'
        
        if User.objects.filter(email=email).exists():
            User.objects.filter(email=email).delete()
            self.stdout.write('Deleted existing user.')
        
        user = User.objects.create_superuser(
            email=email,
            password=password,
        )
        user.is_active = True
        user.is_staff = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Superuser created: {email} / {password}'))