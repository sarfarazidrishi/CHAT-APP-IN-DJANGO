from django.db import models
from django.contrib.auth.models import User, AbstractUser

# Create your models here.
def user_avatar_path(instance, filename):
    return f'accounts/avatars/user_{instance.id}/{filename}'

class CustomUser(AbstractUser):
    avatar= models.FileField(upload_to=user_avatar_path, blank=True, null=True, default='accounts/avatars/default.png')
    bio = models.TextField(blank=True, null=True)
    name= models.CharField(max_length=100, default="user")
    