from django.core.management.base import BaseCommand
from finder.models import ReportService, STATUS_APPROVED

class Command(BaseCommand):
    help = 'Tests all CRUD operations (Create, Read, Update, Delete) against MongoDB Atlas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Testing MongoDB CRUD operations..."))

        # 1. CREATE
        self.stdout.write("1. Testing CREATE (insert_one)...")
        report = ReportService.create_report(
            reporter_id=999,
            reporter_username="test_student",
            report_type="lost",
            title="Blue Dell Laptop Charger",
            category="Electronics",
            description="Lost in Library 2nd Floor reading area.",
            location="Main Campus Library",
            date_lost_found="2026-11-11",
            status=STATUS_APPROVED,
        )
        report_id = report['id']
        self.stdout.write(self.style.SUCCESS(f"   [OK] Created document with ID: {report_id}"))

        # 2. READ
        self.stdout.write("2. Testing READ (find_one)...")
        fetched = ReportService.get_report_by_id(report_id)
        assert fetched is not None, "Failed to retrieve inserted document!"
        assert fetched['title'] == "Blue Dell Laptop Charger", "Document title mismatch!"
        self.stdout.write(self.style.SUCCESS(f"   [OK] Successfully retrieved document: '{fetched['title']}'"))

        # 3. UPDATE
        self.stdout.write("3. Testing UPDATE (update_one)...")
        updated = ReportService.update_report(
            report_id=report_id,
            update_fields={'description': 'Lost in Library 2nd Floor near the window desk.'},
            user_id=999
        )
        assert updated is True, "Failed to update document!"
        fetched_updated = ReportService.get_report_by_id(report_id)
        assert "window desk" in fetched_updated['description'], "Updated text not saved!"
        self.stdout.write(self.style.SUCCESS("   [OK] Successfully updated document description."))

        # 4. STATISTICS & SEARCH
        self.stdout.write("4. Testing SEARCH & STATISTICS...")
        results = ReportService.get_approved_reports(search_query="Dell", category="Electronics")
        assert len(results) >= 1, "Search query failed to match inserted document!"
        stats = ReportService.get_statistics()
        self.stdout.write(self.style.SUCCESS(f"   [OK] Statistics query: {stats}"))

        # 5. DELETE
        self.stdout.write("5. Testing DELETE (delete_one)...")
        deleted = ReportService.delete_report(report_id, user_id=999)
        assert deleted is True, "Failed to delete test document!"
        assert ReportService.get_report_by_id(report_id) is None, "Document still exists after deletion!"
        self.stdout.write(self.style.SUCCESS("   [OK] Successfully deleted test document."))

        self.stdout.write(self.style.SUCCESS("\nAll MongoDB CRUD operations executed successfully on Atlas!"))
