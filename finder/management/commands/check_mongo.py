from django.core.management.base import BaseCommand
from finder.db import test_connection

class Command(BaseCommand):
    help = 'Tests connection to the MongoDB Atlas cluster configured in .env'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Testing connection to MongoDB Atlas..."))
        success, message = test_connection()
        if success:
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] {message}"))
        else:
            self.stdout.write(self.style.ERROR(f"[FAILED] {message}"))
