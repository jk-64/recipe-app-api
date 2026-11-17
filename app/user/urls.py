"""
URL mappings for the user API.
"""
from django.urls import path
from rest_framework.urls import app_name, urlpatterns

from user import views

# app_name to be used by the reverse mapping we defined in the test:
# test_user_api.py > CREATE_USER_URL = reverse('user:create')
app_name = 'user'

urlpatterns = [
    path(
        'create/',

        # The view that handles the request: CreateUserView
        # Because Django expects a function for this parameter,
        # we use as_view() method for rest_framework to convert
        # the class based view to a Django supported view.
        views.CreateUserView.as_view(),

        # The name used by CREATE_USER_URL = reverse('user:create')
        name='create',
    ),

    path(
        'token/',
        views.CreateTokenView.as_view(),
        name='token',
    ),

    path('me/', views.ManageUserView.as_view(), name='me'),
]

