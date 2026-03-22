"""
apps/events/management/commands/seed_data.py

Run with:  python manage.py seed_data
Creates default categories and a superadmin account.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seeds the database with initial categories and a superadmin user'

    def handle(self, *args, **options):
        self._seed_categories()
        self._seed_superadmin()

    def _seed_categories(self):
        from apps.events.models import Category
        categories = [
            ('Workshop',  'workshop'),
            ('Seminar',   'seminar'),
            ('Cultural',  'cultural'),
            ('Sports',    'sports'),
            ('Technical', 'technical'),
            ('Other',     'other'),
        ]
        for name, slug in categories:
            obj, created = Category.objects.get_or_create(slug=slug, defaults={'name': name})
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Category created: {name}'))
            else:
                self.stdout.write(f'  – Category already exists: {name}')

    def _seed_superadmin(self):
        from apps.accounts.models import User
        email = 'admin@eventora.com'
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password='Admin@1234',
                full_name='Super Admin',
                admin_role='Super Admin',
            )
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Superadmin created: {email} / password: Admin@1234'
            ))
            self.stdout.write(self.style.WARNING(
                '  ⚠  Change the superadmin password immediately after first login!'
            ))
        else:
            self.stdout.write(f'  – Superadmin already exists: {email}')
