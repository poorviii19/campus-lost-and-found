import io
import json
from unittest.mock import patch
from bson import ObjectId
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from .models import CATEGORIES, STATUS_APPROVED, STATUS_PENDING, ReportService, get_reports_collection
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
        """Home page should return 200 OK for guest and render landing section."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Official Campus Recovery Hub")
        self.assertContains(response, "Get Started Free")

        # When logged in, should show full dashboard with action buttons
        self.client.force_login(self.student)
        auth_response = self.client.get('/')
        self.assertEqual(auth_response.status_code, 200)
        self.assertContains(auth_response, "Report Lost Item")

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
        self.client.force_login(self.student)
        response = self.client.get('/items/this-is-not-a-valid-id/')
        # Should gracefully redirect to item_list with an error flash message
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/items/')

    def test_nonexistent_objectid_redirects_gracefully(self):
        """Accessing a valid 24-character hex ID that does not exist redirects gracefully."""
        self.client.force_login(self.student)
        response = self.client.get('/items/507f1f77bcf86cd799439011/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/items/')

    def test_custom_404_template_renders(self):
        """Custom 404 page renders cleanly."""
        response = self.client.get('/nonexistent-page-url-xyz/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Lost Your Way?", status_code=404)

    # -------------------------------------------------------------------------
    # 6. Report Discussion Chat Feature Tests
    # -------------------------------------------------------------------------
    def test_chat_unauthenticated_redirects_to_login(self):
        """Anonymous access to chat endpoint redirects to login."""
        response = self.client.get('/reports/507f1f77bcf86cd799439011/chat/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/?next=', response.url)

    @patch('finder.views.ReportService.get_report_by_id')
    def test_chat_nonexistent_report_redirects(self, mock_get_report):
        """Accessing chat for non-existent report ID redirects to item list."""
        mock_get_report.return_value = None
        self.client.force_login(self.student)
        response = self.client.get('/reports/507f1f77bcf86cd799439011/chat/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/items/')

    @patch('finder.views.ReportService.get_report_by_id')
    @patch('finder.views.ReportService.add_message')
    @patch('finder.views.ReportService.get_messages')
    def test_chat_owner_and_admin_access_and_messaging(self, mock_get_messages, mock_add_message, mock_get_report):
        """Report owner and admin can access chat, exchange messages, and query API."""
        mock_report = {
            'id': '507f1f77bcf86cd799439011',
            '_id': ObjectId('507f1f77bcf86cd799439011'),
            'reporter_id': self.student.id,
            'reporter_username': self.student.username,
            'report_type': 'lost',
            'title': 'Test Chat Umbrella',
            'category': 'Accessories',
            'description': 'Black umbrella left in campus library',
            'location': 'Library 2nd Floor',
            'status': 'Approved',
            'messages': []
        }
        mock_get_report.return_value = mock_report
        mock_get_messages.return_value = []
        mock_add_message.return_value = {
            'id': 'abc12345',
            'sender_id': self.student.id,
            'sender_username': self.student.username,
            'sender_role': 'reporter',
            'message': 'Hello admin, any updates on my umbrella?',
            'created_at': 'Nov 20, 2026 01:00 PM',
            'timestamp': '2026-11-20T13:00:00',
        }

        # 1. Owner should be able to view chat page
        self.client.force_login(self.student)
        res_student = self.client.get('/reports/507f1f77bcf86cd799439011/chat/')
        self.assertEqual(res_student.status_code, 200)
        self.assertContains(res_student, "Test Chat Umbrella")
        self.assertContains(res_student, "Chatting as Reporter")

        # 2. Third-party student should be forbidden/redirected
        other_student = User.objects.create_user(
            username='unauthorized_student',
            email='other@campus.edu',
            password='OtherPassword@123'
        )
        self.client.force_login(other_student)
        res_other = self.client.get('/reports/507f1f77bcf86cd799439011/chat/')
        self.assertEqual(res_other.status_code, 302)
        self.assertEqual(res_other.url, '/items/507f1f77bcf86cd799439011/')

        # 3. Campus Admin should be able to view chat page
        self.client.force_login(self.admin)
        res_admin = self.client.get('/reports/507f1f77bcf86cd799439011/chat/')
        self.assertEqual(res_admin.status_code, 200)
        self.assertContains(res_admin, "Chatting as Staff Admin")

        # 4. Student sends a message via POST form
        self.client.force_login(self.student)
        post_res = self.client.post('/reports/507f1f77bcf86cd799439011/chat/', {
            'message': 'Hello admin, any updates on my umbrella?'
        })
        self.assertEqual(post_res.status_code, 302)
        self.assertTrue(mock_add_message.called)

        # 5. Admin sends a reply via JSON API endpoint
        self.client.force_login(self.admin)
        api_post_res = self.client.post(
            '/reports/507f1f77bcf86cd799439011/chat/api/',
            data=json.dumps({'message': 'Yes, someone turned in an umbrella at the front desk.'}),
            content_type='application/json'
        )
        self.assertEqual(api_post_res.status_code, 200)
        api_post_data = api_post_res.json()
        self.assertTrue(api_post_data.get('success'))

        # 6. Query messages via GET API
        mock_report['messages'] = [
            {'message': 'Hello admin, any updates on my umbrella?', 'sender_username': 'teststudent'},
            {'message': 'Yes, someone turned in an umbrella at the front desk.', 'sender_username': 'campusadmin'},
        ]
        api_get_res = self.client.get('/reports/507f1f77bcf86cd799439011/chat/api/')
        self.assertEqual(api_get_res.status_code, 200)
        api_get_data = api_get_res.json()
        self.assertEqual(len(api_get_data.get('messages', [])), 2)
        self.assertEqual(api_get_data['messages'][0]['message'], 'Hello admin, any updates on my umbrella?')
