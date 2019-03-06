from django.db import models

# Create your models here.
class CustomAction(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField()
    thing_uuid = models.CharField(max_length=36)
    action_id = models.CharField(max_length=64)
    data = models.TextField()

    def __str__(self):
        return self.name

class AuthorizationMethod(models.Model):
    name = models.CharField(max_length=64)
    auth_type = models.CharField(max_length=32)
    auth_credentials = models.TextField()

    def __str__(self):
        return self.name

class ThingAuthorization(models.Model):
    thing_uuid = models.CharField(max_length=36, primary_key=True)
    authorization_method = models.ForeignKey(AuthorizationMethod, on_delete=models.CASCADE)
