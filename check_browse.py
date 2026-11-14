import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_lost_found.settings')
sys.path.insert(0, r'c:\Users\HP\OneDrive\Desktop\Lost and Found')
django.setup()

from finder.models import ReportService, STATUS_APPROVED, CATEGORIES

print("=== CATEGORIES in models.py ===")
for c in CATEGORIES:
    print(f"  '{c}'")

print("\n=== ALL REPORTS in MongoDB ===")
all_items = ReportService.get_all_reports()
print(f"Total reports: {len(all_items)}")
for item in all_items:
    print(f"  status='{item.get('status')}' | type='{item.get('report_type')}' | cat='{item.get('category')}' | title='{item.get('title')}'")

print("\n=== APPROVED REPORTS ===")
approved = ReportService.get_approved_reports()
print(f"Count: {len(approved)}")
for item in approved:
    print(f"  id={item.get('id')} | type={item.get('report_type')} | cat={item.get('category')} | loc={item.get('location')} | title={item.get('title')}")

print("\n=== SEARCH TEST (q='') ===")
results = ReportService.get_approved_reports(search_query='', report_type='', category='', location='')
print(f"Results: {len(results)}")

