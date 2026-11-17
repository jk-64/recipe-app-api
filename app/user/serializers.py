"""
Serializers for the user API view.
"""
import email

from django.contrib.auth import (
    get_user_model,
    # Django method allowing the use of its authentication system.
    authenticate,
)

from django.utils.translation import gettext as _

# Import the class that contains tools needed by serializers.
# Serializers are tools to convert objects from/to python objects.
# 1- Takes a JSON input (eg: from an API POST)
# 2- It validates the input as secure and correct for the API
# 3- Convert the JSON either to a Python object or a model for our db
from rest_framework import serializers


# Different base classes can be used as serializers:
# - serializer.Serializer
# - serializers.ModelSerializer
# - ...

# ModelSerializer a base class to create model serializers.
# This class automatically validate and save data to a specific
# model that we define in our serializers.
class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    # This class tells ot Django REST Framework the model and
    # the field and any additional arguments that we want to pass to
    # the serializer. The serializer needs to know which model is
    # representing.
    class Meta:
        # The model that the serializer is representing.
        # Here, it is our user model.
        model = get_user_model()

        # The fields we want to enable for the serializer.
        # This is the fields to create or set when we make a request.
        # The field provided in the request that should be saved in
        # the model that is created.
        # We don't want users to be able to set fields like:
        # - is_active
        # - is_staff
        # - etc
        fields = ['email', 'password', 'name']

        # A dictionary that provide extra metadata to different
        # fields to tell REST Framework things like:
        # - read only field?
        # - write only field?
        # - minimum field length
        # - ...

        # This is part of the data validation process.

        # Password field metadata to be: write only w/ min length.
        # write_only is for security. A user can send a password
        # to be written but, he cannot read it.
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5,  # 400_bad_request if < 5
            },
        }

    # This method override the behavior of the serializer does
    # when it creates a new object.

    # (eg) The default behavior would be to save a password as clear
    # text. We force to pass to a password encryption of our user
    # manager by using create_user()

    # This method called only if the data is successfully validated.
    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)

    # This method is added to hash properly the password
    # when a user is updated.
    # We override the method update() inherited from ModelSerializer
    def update(self, instance, validated_data):
        """Update and return user."""

        # Pop() the password from data dictionary or
        # get None if it does not exist.
        password = validated_data.pop('password', None)

        # Use the ModelSerializer update method on other user data:
        # email and name
        user = super().update(instance, validated_data)

        # If password exists, the user instance hash it
        if password:
            user.set_password(password)
            user.save()

        # returning the user is the expected behavior of the update()
        # for latter usage in the views.
        return user


# Create a serializer specifically for the auth token
# This class is based on the default serializer class. It is not
# based on a model serializer but on a basic serializer not linked
# to any specific model.
class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""

    email = serializers.EmailField()
    password = serializers.CharField(

        # We hide the password text. It is optional as we only use
        # the browser API for testing and development but, it is
        # always nice to have a secure password field when using
        # the API.
        style={'input_type': 'password'},

        # By default, DRF trim the whitespace off the input character
        # field. We don't want to trim the password in case that
        # a user have deliberately set a space at the end of
        # its password. We want to be sure that the system include
        # that space when the password is hashen and saved.
        trim_whitespace=False,
    )

    # Add the logic to authenticate the user that is logged in.
    # This method is called on a serializer at the validation stage
    # of the input by the view.
    def validate(self, attrs):
        """Validate and authenticate the user."""

        # Get the email and password passed to the endpoint.
        email = attrs.get('email')
        password = attrs.get('password')

        # See Django doc regarding authenticate()
        user = authenticate(
            # The context contains header and other stuff.
            # request is a REQUIRED parameter.
            request=self.context.get('request'),
            username=email,
            password=password,
        )

        # If the user is not valid, an error is raised.
        if not user:
            msg = _(
                'Unable to authenticate with provided credentials'
            )

            # Standard way to raise an error with serializers.
            # If we raise the error, the view will return a 400
            raise serializers.ValidationError(
                msg,
                code='authorization',
            )

        # The user is valid, we return it and the view can use it.
        attrs['user'] = user
        return attrs
