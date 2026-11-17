"""
Test for models.
"""
from unittest.mock import patch
from decimal import Decimal

from django.contrib.auth.models import PermissionsMixin
# Base class for test
from django.test import TestCase

# A helper function provided by Django to get the default user model
# This permit to reference the model directly for our custom model.
# If we decide to change the user model, it will be updated
# everywhere in the code.

# Because, as long as we use get_user_model() to retrieve
# the custom user model, we are able to get the default user model
# defined for that project.

# When using Django user model, it is best to use get_user_model()
# in ordre to get references to our custom user model.
from django.contrib.auth import get_user_model

from core import models


def create_user(
        email='user@example.com',
        password='testpass123',
):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test for models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email is successful."""

        # Best practice to use "example.com" as it is a
        # reserved domain name specially for testing.
        email = 'test@example.com'
        password = 'testpass123'

        # The reference to our custom manager is: objects

        # We call our custom user model with get_user_model().
        # Then, our custom manager named 'objects' will call
        # our specific method: create_user().
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        # After calling the manager's method 'create_user()',
        # we should have a user in the system.
        # We assert the correct data in the database.

        # Asserting that the correct email is in the system.
        self.assertEqual(user.email, email)

        # Checking through the hashing system that the password
        # is correctly entered.

        # Then we use the method provided
        # by the default django model: check_password()
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""

        # Create a list of various email addresses.
        # We ensure that those emails are normalized
        # when the model is created.

        # Creation of a list of lists :
        #   [email address, expected normalized email address]

        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],

            # Test2 is normalized with upper case 'T' because
            # in theory, the capitalization of the first part of
            # an email address is unique. This is the main standard
            # of emails. For simplicity, almost all email providers
            # do not allow to have two different email addresses with
            # the same text but with différent capitalization.
            # As we don't know what system the user uses,
            # we have to stuck to the email standardization. Then,
            # we have to support emails with different capitalization
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]

        for email, expected in sample_emails:

            # We don't test the password ane it is: password123
            user = (
                get_user_model()
                .objects
                .create_user(email, 'password123')
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        """
        Test that creating a user without email raise a ValueError.
        """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'password123')

    def test_create_superuser(self):
        """Test creating superuser."""

        user = get_user_model().objects.create_superuser(
            'superuser@example.com',
            'password123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe is successful."""

        # Creating a user assigned to the recipe object
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpassword123',
        )

        # Creation of the recipe
        recipe = models.Recipe.objects.create(
            user=user,
            title='Test recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description.',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test create tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating an ingredient is successful."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Ingredient1',
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generation image patch."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
