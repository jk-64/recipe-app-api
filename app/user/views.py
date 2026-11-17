"""
Views for the user API.
"""
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


# Import an existing view provided by DRF for creating the tokens.
# This saves us time to create the associated logic.
# We just have to override some parts of it.
class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""

    # We customize the serializer to use the custom one we created
    # because the token view uses the username and password instead
    # of email and password. We want to customize it be email and
    # password inside our serializers. We override the defaut
    # serializer used by the default auth token view.
    serializer_class = AuthTokenSerializer

    # This rendering class is totally optional.
    # It uses the default render class for the token view.
    # Without it, would not get the nice api GUI used by DRF.
    # Adding it manually make it sure it is enabled inside the view.
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


# RetrieveUpdateAPIView this class contains the functionalities for
# retrieving and updating an object.
# - Retrieving: GET
# - Updating: PUT or PATCH
class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""

    # We use the same serializer as the CreateUserView
    serializer_class = UserSerializer

    # DRF uses two distincts authentications on a user.
    # 1- 'authentication' to be certain about the user's identity
    # 2- 'permissions' to know what the user is allowed to do

    # We use TokentAuthentication to identify the request.user
    authentication_classes = [authentication.TokenAuthentication]

    # We use IsAuthenticated to be certain that the user is
    # authenticated
    permission_classes = [permissions.IsAuthenticated]

    # We override the method: get_object()
    # Use GET to retrieve an object in the API.
    # Here, the user attached to the request.
    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user
