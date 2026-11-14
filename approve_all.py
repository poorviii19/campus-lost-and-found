import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_lost_found.settings')
sys.path.insert(0, r'c:\Users\HP\OneDrive\Desktop\Lost and Found')
django.setup()

from finder.models import ReportService, STATUS_APPROVED

# Get all pending reports and approve them
all_reports = ReportService.get_all_reports()
print(f"Total reports: {len(all_reports)}")

approved_count = 0
for report in all_reports:
    if report.get('status') != STATUS_APPROVED:
        success = ReportService.update_status(report['id'], STATUS_APPROVED)
        status_icon = "[OK]" if success else "[FAIL]"
        print(f"  {status_icon} Approved: '{report.get('title')}' (was: {report.get('status')})")
        if success:
            approved_count += 1
    else:
        print(f"  [SKIP] Already approved: '{report.get('title')}'")

print(f"\nApproved {approved_count} report(s).")
print("\nVerifying approved count now:")
approved = ReportService.get_approved_reports()
print(f"Approved reports visible on Browse page: {len(approved)}")
for item in approved:
    print(f"  - {item.get('title')} | type={item.get('report_type')} | cat={item.get('category')}")

