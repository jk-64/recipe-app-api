"""
Views for the recipe APIs.
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers


# Adding the documentation changes
@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description="Comma separated list of tag IDs to filter.",
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description=(
                        "Comma separated list of ingredient IDs to filter.",
                )
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""

    # We define what we need to use from the system
    serializer_class = serializers.RecipeDetailSerializer

    # The queryset permit the get the objects
    # that our view will manipulate.
    queryset = Recipe.objects.all()

    # Set Authentication and permissions for the view usage
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Convert to integer the string of ids given by the URL of
    # coma separated  string parameters: "1,2,3" -> [1,2,3]
    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    # We override the get_queryset() to filter the recipes
    # that belong to the authenticated user.
    def get_queryset(self):
        """Retrieve recipes for authenticated user."""

        # Grab the IDs present in the GET request used to filter
        # the recipes by Tag or by Ingredients
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')

        # A filter returns a new queryset.
        # When we do queryset.filter(...) we change queryset
        # but self.queryset stay unchanged.
        queryset = self.queryset

        # If existed, the params are converted f/ string to integer
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(
                ingredients__id__in=ingredient_ids
            )

        # It is important not to use self.queryset.
        # We return the queryset we filtered by tags or ingredients.
        # REM: original queryset - see: II p 43 -
        return (
            queryset
            .filter(user=self.request.user)
            .order_by('-id').distinct()
        )

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload_image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter by items assigned to recipes."
            )
        ]
    )
)
class BaseRecipeAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for the recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # We override the queryset method to be sure that we return
    # the queryset object ONLY FOR the authenticated user.
    # By default, the queryset returns all the tags that exist
    # in the database, regardless of the creator.
    def get_queryset(self):
        """Filter request to authenticated user."""

        # Adding the assigned_only parameter to the query
        # Assign only is a boolean and get() returns its value
        # if it exists or a default value set to 0.
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )

        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        # When we return object, it is preferable to be explicit
        # because the database version or database brand may return
        # a different order.
        return (
            queryset
            .filter(user=self.request.user)
            .order_by('-name')
            .distinct()
        )


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
