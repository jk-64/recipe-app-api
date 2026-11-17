"""
Database models.
"""
import uuid
import os

from django.conf import settings

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models  # noqa
from django.contrib.auth.models import (
    AbstractBaseUser,  # Functionalities for auth system (no fields)
    BaseUserManager,
    PermissionsMixin,  # Functionalities for permissions and fields
)


# instance: the object the image is uploaded to.
# filename: the original image name.
def recipe_image_file_path(instance, filename):
    """Generate file path for new recipe image."""
    ext = os.path.splitext(filename)[1]  # ext: extension
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'recipe', filename)


# subclassing BaseUserManager, that uses an email as the unique
# identifier instead of a username
class UserManager(BaseUserManager):
    """Manager for the users."""

    # Method to create a user.
    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""

        # ValueError is a built-in exception. No need to import it.
        # The if-guard will raise an exception if the email is blank
        if not email:
            raise ValueError('User must have an email address.')

        # The base user manager provide the method: normalize_email()
        user = (
            self.model(
                email=self.normalize_email(email),
                **extra_fields)
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    # This methode must be written correctly because it will be
    # used by the Django CLI
    def create_superuser(self, email, password):
        """Create and return a new superuser."""

        # Use the above methode first
        user = self.create_user(email, password)

        # The PermissionsMixin provides the field: is_superuser
        # - Staff to access Django admin site
        # - Superuser to access EVERYTHING in the Django admin site
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)

        return user


# AbstractUser: to use the existing fields on the user model and
# to remove the username field or others.
#
# AbstractBaseUser: to start from scratch by creating a completely
# new user model.
class User(AbstractBaseUser, PermissionsMixin):
    """Custom User in the system."""

    # Fields needed for the user
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    # is_staff permit to log into the Django Admin
    is_staff = models.BooleanField(default=False)

    # Assigning the custom object manager to the custom User
    objects = UserManager()

    # Define the field our custom model uses for authentication.
    # This field replace the default field: username
    USERNAME_FIELD = 'email'


class Recipe(models.Model):
    """Recipe object."""

    # Store the user the recipe belongs to.
    # FK establishes a relationship between the recipe model and
    # the user model.
    user = models.ForeignKey(
        # We can get the user from a sting but, BEST PRACTICE
        # is to get the user model from the settings file.
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    title = models.CharField(max_length=255)

    # See TextField() and MySQL
    description = models.TextField(blank=True)

    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    # Image associated to the recipe
    image = models.ImageField(
        null=True,
        upload_to=recipe_image_file_path,
    )

    # A recipe can have many tags, ingredients
    # A tag, ingredients can be associated to many recipes
    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField('Ingredient')

    def __str__(self) -> str:
        return self.title


class Tag(models.Model):
    """Tag for filtering recipes."""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,

        # If user is deleted, associated tag is also deleted
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient for recipes."""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,

        # If user is deleted, associated tag is also deleted
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name
