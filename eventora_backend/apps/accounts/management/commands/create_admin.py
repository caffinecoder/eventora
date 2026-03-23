from django.core.management.base import BaseCommand
from apps.accounts.models import User

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not User.objects.filter(email='admin@eventora.com').exists():
            User.objects.create_superuser(
                email='admin@eventora.com',
                password='yourpassword',
                full_name='Admin',
                role='admin'
            )
            self.stdout.write('Admin created')
        else:
            self.stdout.write('Admin already exists')