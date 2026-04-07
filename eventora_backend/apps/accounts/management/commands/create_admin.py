from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        email    = 'admin@eventora.com'
        password = 'Admin1234'

        if User.objects.filter(email=email).exists():
            User.objects.filter(email=email).delete()
            self.stdout.write('Deleted existing admin.')

        User.objects.create_superuser(
            email      = email,
            password   = password,
            full_name  = 'Super Admin',
            role       = 'admin',
            admin_role = 'Super Admin',
            is_active  = True,
            is_staff   = True,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Superuser created: {email} / {password}'
        ))