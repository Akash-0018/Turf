from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_user'
        
    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # If the user is a superuser, automatically make them an admin
        if self.is_superuser:
            self.is_admin = True
        super().save(*args, **kwargs)
