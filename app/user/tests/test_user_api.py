"""Test for the user API."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

# Adding the URL API to be tested as a constant
# because it will be used by several tests.

# We use reverse to grab the full URL path from the name
# of the view that we want the URL for.
# The schema 'app_name:path_name' correspond to endpoint name.
# https://docs.djangoproject.com/en/6.0/topics/
# http/urls/#topics-http-reversing-url-namespaces - doc 5.2 p271 -
CREATE_USER_URL = reverse('user:create')

# endpoint for creating tokens
TOKEN_URL = reverse('user:token')

# endpoint for managing profils
ME_URL = reverse('user:me')


# Set a helper function to create a user to use for testing.
# This avoids to use a respective coding at each test.

# **params: any dictionary with parameters regarding the user.
# This adds flexibility to add any parameter to the function call
# that we can pass through the user we are creating.
def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


# Define two test classes for two categories:
# - public test: about unauthenticated requests
# (eg: registering a new user)
# - private test: about authenticated requests

class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        # Create an APIClient object to send request to Django server
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""

        # Create a test payload dictionary to pass to the API
        # for the test
        # payload: inputs to the API - see I p159 -
        payload = {
            'email': 'user@example.com',
            'password': 'userpassword123',
            'name': 'User Test',
        }

        # POST the data to the create user endpoint
        res = self.client.post(CREATE_USER_URL, payload)

        # The HTTP 201 Created successful response status code
        # indicates that the HTTP request has led to the creation
        # of a resource. This status code is commonly sent as
        # the result of a POST request.
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Retrieve the object in the database that has the email
        # address we passed with the payload to validate that
        # the object was created in the database after we did
        # the post
        user = get_user_model().objects.get(email=payload['email'])

        # We use the Django user method to check that the password
        # has been correctly created in the database.
        self.assertTrue(user.check_password(payload['password']))

        # For security reason, we check that the password has not
        # been sent back to the user after it has been created.
        # It is mainly done in case that after a code change,
        # we send it back. Future-proof!
        self.assertNotIn('password', res.data)

    # Test if a user with the email is already in the db
    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""

        payload = {
            'email': 'user@example.com',
            'password': 'userpassword123',
            'name': 'User Test',
        }

        # A first user is created in the database with UserManager
        create_user(**payload)

        # POST request to create a second user with the same data
        res = self.client.post(CREATE_USER_URL, payload)

        # Check that we received a 400 error code
        self.assertEqual(
            res.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    # Test the password length
    def test_password_too_short_error(self):
        """Test an error is return if password less than 5 chars."""

        payload = {
            'email': 'user@example.com',
            'password': 'pw',
            'name': 'User Test',
        }

        # POST request to create the user
        res = self.client.post(CREATE_USER_URL, payload)

        # Check that we received a 400 error code
        self.assertEqual(
            res.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        # Check that the user is not in the db
        user_exits = (
            get_user_model()
            .objects
            .filter(email=payload['email'])
            .exists()  # return a boolean. True if exists.
        )
        self.assertFalse(user_exits)  # exists() returned: False

    # Test the successful case when we log in or use the token API
    # to create a new token.
    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""

        user_details = {
            'email': 'user@example.com',
            'password': 'userpassword123',
            'name': 'Test Name',
        }

        create_user(**user_details)

        # Create a payload to send to the token API
        # in order to log in.
        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }

        res = self.client.post(TOKEN_URL, payload)

        # Check that the response includes a token
        self.assertIn('token', res.data)
        # Check that the satus code is 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # Testing the bad password credential case
    def test_create_token_bad_credentials(self):
        """Test return error if credentials invalid."""

        create_user(email='test@example.com', password='goodpassw')

        payload = {
            'email': 'test@example.com',
            'password': 'badpassw',
        }

        res = self.client.post(TOKEN_URL, payload)

        # Check that no token has been returned
        self.assertNotIn('token', res.data)
        # Check a 400 status code for an unsuccessful log in
        self.assertEqual(
            res.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    # Similar test as above with a blank password
    def test_create_token_with_blank_password(self):
        """Test posting a blank password returns an error."""

        payload = {
            'email': 'test@example.com',
            'password': '',
        }

        res = self.client.post(TOKEN_URL, payload)

        # Check that no token has been returned
        self.assertNotIn('token', res.data)
        # Check a 400 status code for an unsuccessful log in
        self.assertEqual(
            res.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # Test that authentication is required and enforce
    # for the endpoint: 'me'
    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for user."""

        # The client do an unauthenticated request to the API
        # Indeed, in setUp(), the client is instantiated
        # w/o a logged-in user.
        res = self.client.get(ME_URL)

        # If the client is recognized as unauthenticated by
        # the system, it is not authorized to connect to
        # the endpoint: me. The response status should be 401.
        self.assertEqual(
            res.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


# Create a class for the private side of the API.
# Private: the user is authenticated
class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    # We separate the test in two part because we gonna set up
    # the authentication before each test. This avoids code
    # duplication for authentication or mocking authentication
    # with the API.
    def setUp(self):

        # Create a user to use for the tests
        self.user = create_user(
            email='user@example.com',
            password='userpassword123',
            name='Test Name',
        )

        # Instantiate a client provided by DRF
        self.client = APIClient()

        # force_authenticate() for a specific user.
        # We don't do real authentication because it is unnecessary
        # for the unittests. We isolate the unittest to a specific
        # function to test. No need to test the authentication system
        # for every single request.

        # With force_authenticate() any request done with this
        # 'client' will be authenticated with the 'user' we defined
        # above.
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logging user."""

        # Retrieve the details of the authenticated user
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the endpoint: me."""

        # POST should be only used when creating objects
        # in the system. The endpoint 'me' is not designed to create
        # object (the endpoint 'create' is design for it). Then, the
        # API should disable the POST method for the endpoint: me.

        # With this API endpoint, we will only modify.
        # Then, we will use the methods: PUT and PATCH.
        res = self.client.post(ME_URL, {})

        self.assertEqual(
            res.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_update_user_profile(self):
        """
        Test updating the user profile for the authenticated user.
        """

        # The payload to update name and password of the
        # authenticated user.
        # REM: it is not mandatory to change both in the same time!
        payload = {
            'name': 'Updated Name',
            'password': 'newpassword123',
        }

        # Authentication with the set-up defined user to update it
        # using the PATCH method and the payload dict.
        res = self.client.patch(ME_URL, payload)

        # By default, the user's value are not refreshed automatically
        # Then, we have to call refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check if the user's name and password have been updated.
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(
            self.user.check_password(payload['password'])
        )
