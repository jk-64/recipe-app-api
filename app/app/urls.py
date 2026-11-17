"""
URL mapping for the project.
"""
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # To retrieve settings
from django.conf.urls.static import static  # To use static URLs

# from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Because it is only for test purposes, we add the url here
    # path(
    #     'api/health-check/',
    #     core_views.health_check,
    #     name='health-check',
    # ),

    # Path that generate the schema file associated with the project
    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='api-schema',
    ),

    # url_name indicates the schema to use when loading Swagger.
    # It indicates the URL we defined above.
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='api-schema'),
        name='api-docs',
    ),

    path('api/user/', include('user.urls')),
    path('api/recipe/', include('recipe.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
