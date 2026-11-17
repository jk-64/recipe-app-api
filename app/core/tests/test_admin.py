"""
Test for the Django Admin modifications.
"""
from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    """Tests for Django Admin."""

    # Adding a set-up method for the tests
    # This will allow us to set up modules at the beginning of
    # the different tests that we will add to the class.

    # REM: The unittest module for python uses different syntax
    # than the one normally used. Python normally use for methods
    # 'snake_case' but, for the built-in unittest it uses camelCase.

    # Code to run before each test - Mind the camelCase -
    # Creation of two users in the database: superuser + user
    def setUp(self):
        """Create user and client"""

        # Create an instance of the Django test client.
        # This object permits to do HTTP requests.
        self.client = Client()

        # Create a superuser to authenticate with
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='password123',
        )

        # Force the client instance to log into the Django Admin
        # using the superuser.
        self.client.force_login(self.admin_user)

        # We create a regular user.
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='password123',
            name='Test User'
        )

    # Adding a first test
    def test_users_list(self): ...

    def test_edit_user_page(self): ...

    def test_create_user_page(self):
        """Test the create user page works."""

        # Getting a URL from the Django admin according to Django
        # Documentation. Paragraph: Reversing admin URLs

        # https://docs.djangoproject.com/en/5.2/ref/contrib/admin/
        # {{ app_label }}_{{ model_name }}_add

        # REM: no need to pass an argument like the 'id' (as above)
        # because we are creating a new user.
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        # Ensure the page is load successfully
        self.assertEqual(res.status_code, 200)
