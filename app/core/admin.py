"""
Django Admin customization
"""
from django.contrib import admin

# Importing the user admin base class that is used for the default
# Django Authentication system to make some changes to it.
# We change its name to BaseUserAdmin to avoid any conflict because
# it is more convenient for us to call the class managing our
# customized user: UserAdmin.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# import the translation package integrated to Django.
# This permit to translate the text in the app using: '_'
# The gettext_lazy() method become: _() to ease code readability.

# It is always best practice to do it for future proofing,
# even if we don't do any translation as in this actual project.
from django.utils.translation import gettext_lazy as _

# Importing the custom modules we want to register with Django Admin
from core import models


# Subclassing BaseUserAdmin to personalize order and displayed fields
# The default UserAdmin uses the default model manager with simple
# create-read-update operations and would not apply the changes
# we specify as the ordering and the list_display.
class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['email', 'name']

    # fieldsets: for fields to be used in editing users

    # We modify the fieldsets to include only the fields
    # we created in model > User or the fields integrated with
    # the permission mixin.

    # This override the fields created by the Django default user.
    fieldsets = (
        # Arguments corresponding to - I p 137 -
        # (Heading, {fields: ('field_name', 'field_name', ...)})
        # REM: Headings are personalized
        (
            None,  # Heading
            {
                'fields': (
                    'email',
                    'password'
                )
            }
        ),

        # Usage of the translation because
        # Heading value is not None as above
        (
            _('Permission'),  # Heading
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),

        # Usage of the translation because
        # Heading value is not None as above
        (
            # _('Important dates - Headings are personalized'),
            _('Important dates'),
            {
                'fields': (
                    'last_login',
                )
            }
        ),
    )

    readonly_fields = ['last_login']

    # add_fieldsets: for fields to be used when creating a user

    # add_fieldsets is not a standard ModelAdmin attribute.
    # UserAdmin overrides get_fieldsets to use this attribute
    # when creating a user.


    # https://docs.djangoproject.com/en/5.2/topics/
    # auth/customizing/#custom-users-and-django-contrib-admin
    add_fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )


# Register the Custom User model to use the subclassed BaseUserAdmin
# admin.site.register(models.ModelName [,ModelRepInAdminInterface])
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)
admin.site.register(models.Tag)
admin.site.register(models.Ingredient)


