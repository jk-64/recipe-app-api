"""
Test for the tags API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


# Function to grab tag with the 'id'
def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('recipe:tag-detail', args=[tag_id])


# Create a sample user
# REM: we have code duplication creating user. In general, we should
# avoid duplication. In testing, we may have to personalize the user
# object depending on the tested object.
def create_user(
        email='user@example.com',
        password='password123'
):
    """Create and return a user."""
    return (
        get_user_model()
        .objects
        .create_user(
            email=email,
            password=password,
        )
    )


class PublicTagApiTests(TestCase):
    """Test unauthenticated API requests."""

    # Create a client without authenticated user
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""

        res = self.client.get(TAGS_URL)

        self.assertEqual(
            res.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class PrivateTagsAPITest(TestCase):
    """Test authenticated API requests."""

    # Create a client with an authenticated user
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()

        # The user is authenticated with the client
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        # Sample tags created for the test
        Tag.objects.create(user=self.user, name='test_vegan')
        Tag.objects.create(user=self.user, name='test_desert')

        # Execute the code by calling the api
        res = self.client.get(TAGS_URL)

        # REM: We do order_by('-name') to be db agnostique.
        # Not only Postgres vs MySQL, it can also be
        # Postgres 14 vs Postgres 12.

        # Any db can have different return order. Being explicit
        # permit to be certain to obtain the same answer.
        tags = Tag.objects.all().order_by('-name')

        # We pass the return from the query through the serializer
        # We expect a list of objects: many=True
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='user2 fruity')

        tag = Tag.objects.create(user=self.user, name='user food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # A list of tags is returned.
        self.assertEqual(len(res.data), 1)

        # First tag is at the list index [0]
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag."""

        # Test preparation by creation of a tag
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        # Execution of the test request

        # Prepare the test with the payload and the url corresponding
        # to the tag we want to update (patch).
        payload = {'name': 'Dessert'}
        url = detail_url(tag.id)

        # Perform the request to patch() the tag
        res = self.client.patch(url, payload)

        # Test assertions
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Explicitly refresh the data from the db, as it is not done
        # automatically by the test framework and the tag name would
        # be the one we created in the first place.
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting tag."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        url = detail_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tag = Tag.objects.filter(user=self.user)
        self.assertFalse(tag.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags by those assigned to recipes."""
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")
        recipe = Recipe.objects.create(
            title='Green Egggs on Toast',
            time_minutes=10,
            price=Decimal('2.50'),
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Dinner')
        rec1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=Decimal('5.00'),
            user=self.user,
        )
        rec2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=Decimal('2.00'),
            user=self.user,
        )
        rec1.tags.add(tag)
        rec2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        # We have the tag 'Breakfast' assigned to two recipes.
        # We want to be certain that no tag duplication is
        # returned as we use on the queryset the method distinct()
        self.assertEqual(len(res.data), 1)


