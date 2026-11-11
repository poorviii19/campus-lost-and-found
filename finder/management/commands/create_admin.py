from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a default campus administrator account (or updates existing) for testing the Admin Portal'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@campus.edu'
        password = 'AdminPass@2026'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True}
        )

        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"✔ Created admin user '{username}' with password '{password}'"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✔ Updated existing user '{username}' to superuser/staff with password '{password}'"))

