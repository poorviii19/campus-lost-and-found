import io
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from .models import CATEGORIES, STATUS_APPROVED, STATUS_PENDING
from .forms import StudentRegistrationForm, ItemReportForm


class CampusLostAndFoundTests(TestCase):
    """
    Automated Test Suite for Campus Lost & Found Portal:
    Covers Home, Auth, Security, Form Validation, and Error Boundaries.
    """

    def setUp(self):
        self.client = Client()
        # Create a standard student user in SQLite
        self.student = User.objects.create_user(
            username='teststudent',
            email='student@campus.edu',
            password='TestPassword@123'
        )
        # Create a campus staff administrator in SQLite
        self.admin = User.objects.create_user(
            username='campusadmin',
            email='admin@campus.edu',
            password='AdminPassword@123',
            is_staff=True,
            is_superuser=True
        )

    # -------------------------------------------------------------------------
    # 1. Home Page Tests
    # -------------------------------------------------------------------------
    def test_home_page_renders_successfully(self):
        """Home page should return 200 OK and render brand hero section."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lost Something?")
        self.assertContains(response, "Report Lost Item")
        self.assertContains(response, "Report Found Item")

    # -------------------------------------------------------------------------
    # 2. Authentication Flow Tests
    # -------------------------------------------------------------------------
    def test_student_registration_and_login(self):
        """Student registration creates a record in SQLite and logs the user in."""
        response = self.client.post('/register/', {
            'username': 'newstudent',
            'email': 'newstudent@campus.edu',
            'password1': 'StrongPass@2026',
            'password2': 'StrongPass@2026',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newstudent').exists())

    def test_login_with_invalid_credentials_fails(self):
        """Invalid credentials should not log the user in and show error message."""
        response = self.client.post('/login/', {
            'username': 'teststudent',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_login_and_logout_flow(self):
        """Valid credentials log in the user, and logout flushes the session."""
        login_res = self.client.post('/login/', {
            'username': 'teststudent',
            'password': 'TestPassword@123',
        })
        self.assertEqual(login_res.status_code, 302)

        # Check authenticated navbar
        home_res = self.client.get('/')
        self.assertContains(home_res, "teststudent")
        self.assertContains(home_res, "Logout")

        # Logout
        logout_res = self.client.get('/logout/')
        self.assertEqual(logout_res.status_code, 302)
        home_after_logout = self.client.get('/')
        self.assertContains(home_after_logout, "Log in")

    # -------------------------------------------------------------------------
    # 3. Access Control & Page Protection Tests
    # -------------------------------------------------------------------------
    def test_protected_pages_redirect_anonymous_users(self):
        """Unauthenticated requests to /report/ and /my-reports/ redirect to /login/."""
        res_report = self.client.get('/report/')
        self.assertEqual(res_report.status_code, 302)
        self.assertIn('/login/?next=/report/', res_report.url)

        res_my_reports = self.client.get('/my-reports/')
        self.assertEqual(res_my_reports.status_code, 302)
        self.assertIn('/login/?next=/my-reports/', res_my_reports.url)

    def test_admin_portal_blocks_non_staff_students(self):
        """Standard students should be denied access to /portal-admin/."""
        self.client.force_login(self.student)
        response = self.client.get('/portal-admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/?next=/portal-admin/', response.url)

    def test_admin_portal_accessible_to_staff(self):
        """Staff administrators can access /portal-admin/."""
        self.client.force_login(self.admin)
        response = self.client.get('/portal-admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff Administration Portal")

    # -------------------------------------------------------------------------
    # 4. Input & File Upload Validation Tests
    # -------------------------------------------------------------------------
    def test_item_report_form_valid_data(self):
        """ItemReportForm validates clean data correctly."""
        form = ItemReportForm(data={
            'report_type': 'lost',
            'title': 'Leather Wallet',
            'category': 'Accessories',
            'description': 'Brown leather wallet with college ID inside',
            'location': 'Cafeteria',
            'date_lost_found': '2026-11-11',
        })
        self.assertTrue(form.is_valid())

    def test_item_report_form_rejects_empty_required_fields(self):
        """ItemReportForm should reject submissions missing required fields."""
        form = ItemReportForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('category', form.errors)
        self.assertIn('location', form.errors)

    def test_image_validation_rejects_non_image_files(self):
        """Uploading a fake or corrupt file should be caught by Pillow verification."""
        fake_file = SimpleUploadedFile('document.txt', b'This is plain text, not an image.', content_type='text/plain')
        form = ItemReportForm(
            data={
                'report_type': 'found',
                'title': 'Found USB Drive',
                'category': 'Electronics',
                'description': 'Found near library printer',
                'location': 'Library 1st floor',
                'date_lost_found': '2026-11-11',
            },
            files={'image': fake_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_image_validation_accepts_valid_image(self):
        """Uploading a valid JPEG image passes Pillow validation."""
        img_io = io.BytesIO()
        Image.new('RGB', (80, 80), color='green').save(img_io, format='JPEG')
        img_io.seek(0)
        valid_file = SimpleUploadedFile('valid.jpg', img_io.read(), content_type='image/jpeg')

        form = ItemReportForm(
            data={
                'report_type': 'lost',
                'title': 'Scientific Calculator',
                'category': 'Electronics',
                'description': 'Casio fx-991EX',
                'location': 'Math Building',
                'date_lost_found': '2026-11-11',
            },
            files={'image': valid_file}
        )
        self.assertTrue(form.is_valid())

    # -------------------------------------------------------------------------
    # 5. Error Boundaries & Malformed Input Tests
    # -------------------------------------------------------------------------
    def test_invalid_objectid_in_url_redirects_gracefully(self):
        """Accessing a malformed MongoDB ObjectId in the URL should not trigger a 500 server crash."""
        response = self.client.get('/items/this-is-not-a-valid-id/')
        # Should gracefully redirect to item_list with an error flash message
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/items/')

    def test_nonexistent_objectid_redirects_gracefully(self):
        """Accessing a valid 24-character hex ID that does not exist redirects gracefully."""
        response = self.client.get('/items/507f1f77bcf86cd799439011/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/items/')

    def test_custom_404_template_renders(self):
        """Custom 404 page renders cleanly."""
        response = self.client.get('/nonexistent-page-url-xyz/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Lost Your Way?", status_code=404)
