from django.contrib import admin
from .models import AuthorizationMethod, CustomAction

# Register your models here.

admin.site.register(CustomAction)
admin.site.register(AuthorizationMethod)
