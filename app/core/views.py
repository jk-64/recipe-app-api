"""
Core views for app.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response


# When the API send a simple response, we can use the decorator
# and write a function that acts as a view.
@api_view(['GET'])
def health_check(request):
    """Returns successful response."""
    return Response({'healthy': True})
