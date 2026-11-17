"""
Test for recipe APIs.
"""
import tempfile
import os

from PIL import Image
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

from user import serializers

RECIPES_URL = reverse('recipe:recipe-list')


# Create an URL from the recipe's id
def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


# Generate URL to the upload image endpoint
def image_upload_url(recipe_id):
    """Create and return an image upload URL."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


# The function accepts dynamic parameters with **params
def create_recipe(user, **params):
    """Create and return a sample recipe."""

    # Set default values if there is no **params
    # because in many tests we don't need to specify a recipe.
    # If we need some values to test, we will override as needed.
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }

    # A dictionary should not be changed in programming because
    # that may affect other parts of the code. The solution is
    # to use update().
    # update() contains the **params data that will override or add
    # keys in the 'defaults' dictionary we just created above.
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


# Create multiple users for testing
def create_user(**params):
    """Create and return a new user."""

    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    # Create a set-up method that instantiate a client without
    # any authenticated user.
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""

        res = self.client.get(RECIPES_URL)

        self.assertEqual(
            res.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    # Create a set-up method that instantiate a client with
    # an authenticated user.
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpassword123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""

        # We create two recipes linked to the user
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        # We call the database to return the list of two recipes
        res = self.client.get(RECIPES_URL)

        # We expect the recipe list with the most recent on top using
        # reverse order of the ids
        recipes = Recipe.objects.all().order_by('-id')

        # We expect the result to match whatever
        # the serializer returns.

        # A serializer can return:
        # - a detail: one item
        # - a list of items: many=True to precise that
        # we pass in a list of items.
        serializer = RecipeSerializer(recipes, many=True)

        # Check a status 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # We expect that the database response is the same as
        # the recipe object passed through the serializer.
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""

        # We create a second user
        other_user = create_user(
            email='other@example.com',
            password='testpassword123',
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)  # The authenticated user

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        # Check a status 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # We expect that the database response is the same as
        # the recipe object passed through the serializer.
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        # REM: we pass a unique recipe. No need of many=True
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating recipe. """

        # We define the fields to pass to the API.
        payload = {
            'title': 'sample recipe creation',
            'time_minutes': 30,
            'price': Decimal('5.99'),
            'description': 'test description',
        }

        # To create a recipe, we need to pass a post() request
        # with a payload to the following URL: /api/recipes/recipe/
        res = self.client.post(RECIPES_URL, payload)

        # We check if the recipe has been created as expected
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # We get the recipe by the 'id'
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""

        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link,
            description='sample recipe description'
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload)

        # Test the update of the recipe
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of recipe."""

        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='sample recipe description'
        )

        payload = {
            'title': 'New recipe title',
            'link': 'http://example.com/new-recipe.pdf',
            'description': 'New sample description',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }

        url = detail_url(recipe.id)

        # For a full update (every single field),
        # we use the HTTP method: PUT
        res = self.client.put(url, payload)

        # Test the update of the recipe
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # To compare the payload and the recipe from db,
        # we reload the recipe
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_id_do_not_change_the_user(self):
        """Test changing user id don't change the user."""

        new_user = create_user(
            email='user2@example.com',
            password='user2pwd123',
        )

        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)

        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful."""

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Recipe.objects.filter(id=recipe.id).exists()
        )

    def test_delete_another_user_recipe_gives_error(self):
        """
        Test trying to delete another user's recipe gives error.
        """

        new_user = create_user(
            email='new_user@example.com',
            password='newuserpass123',
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Recipe.objects.filter(id=recipe.id).exists()
        )

    def test_create_recipe_with_new_tags(self):
        """Test creating recipe with new tags."""

        # Test set-up
        payload = {
            'title': 'Test curry',
            'description': 'test description',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }

        # Because we have a nested object (tags), we want to be
        # certain that it is converted to a JSON format to get
        # a successful POST to the API
        res = self.client.post(RECIPES_URL, payload, format='json')

        # Test result of the test
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Grab user's recipes from db
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)

        # We extract the unique recipe from the db response
        recipe = recipes[0]

        # We check that there is two tags in it.
        self.assertEqual(recipe.tags.count(), 2)

        # We compare if the tags in the payload are the same as
        # the tags from the db.
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""

        # Prepare the test
        tag_indian = Tag.objects.create(
            user=self.user,
            name='Indian'
        )

        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'description': 'test description',
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }

        # Execute the test
        res = self.client.post(RECIPES_URL, payload, format='json')

        # Check the test results
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        # Ensure that the 'tag_indian' is present
        # in the returned tags
        self.assertIn(tag_indian, recipe.tags.all())

        # We compare if the tags in the payload are the same as
        # the tags from the db.
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updation a recipe."""
        tag_breakfast = Tag.objects.create(
            user=self.user,
            name='Breakfast'
        )
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {
            'title': 'Cauliflower Tacos',
            'description': 'test description',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
            'ingredients': [
                {'name': 'Cauliflower'},
                {'name': 'Salt'},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredients."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Lemon'
        )
        payload = {
            'title': 'Vietnamese Soup',
            'description': 'test description',
            'time_minutes': 25,
            'price': Decimal('2.55'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
            'ingredients': [
                {'name': 'Lemon'},
                {'name': 'Fish Sauce'},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name': 'Limes'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(
            user=self.user,
            name='Limes',
        )
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """
        Test assigning an existing ingredient when updating a recipe.
        """
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='Pepper',
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name='Chili',
        )
        payload = {'ingredients': [{'name': 'Chili'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipes ingredients."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Garlic',
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)
        payload = {'ingredients': []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags."""
        r1 = create_recipe(
            user=self.user,
            title='Thai Vegetable Curry',
        )
        r2 = create_recipe(
            user=self.user,
            title='Aubergin whit Tahini',
        )
        r3 = create_recipe(
            user=self.user,
            title='Fish and chips',
        )
        tag1 = Tag.objects.create(user=self.user, name='vegan')
        tag2 = Tag.objects.create(user=self.user, name='vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering recipes by ingredients."""
        r1 = create_recipe(
            user=self.user,
            title='Posh Beans on Toast',
        )
        r2 = create_recipe(
            user=self.user,
            title='Chicken Cacciatore',
        )
        r3 = create_recipe(
            user=self.user,
            title='Red Lentil Dal',
        )
        ing1 = Ingredient.objects.create(
            user=self.user,
            name='Feta Cheese',
        )
        ing2 = Ingredient.objects.create(
            user=self.user,
            name='Chicken',
        )
        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)

        params = {'ingredients': f'{ing1.id},{ing2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Test for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as img_file:
            img = Image.new('RGB', (10, 10))
            img.save(img_file, format='JPEG')
            img_file.seek(0)
            payload = {'image': img_file}

            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'a string is not an image'}

        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(
            res.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


