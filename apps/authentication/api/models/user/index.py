from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from apps.base.utils.index import gen_uuid

class UserManager(BaseUserManager):
    def create_user(self,first_name: str, last_name: str, email: str,password: str = None,
                    is_staff=False, is_superuser=False, description: str = None) -> "User":

        if not email:
            raise ValueError('Users must have an email address')
        if not password:
            raise ValueError('Users must have a password')

        user              = self.model(email=self.normalize_email(email))
        user.first_name   = first_name
        user.last_name    = last_name
        user.description  = description
        user.is_active    = True
        user.is_staff     = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, first_name: str, last_name: str,email: str, password: str) -> "User":
        account = User(id=gen_uuid(), email=email, first_name=first_name, last_name=last_name, is_staff=True, 
                        is_superuser=True)
        account.set_password(password)
        account.save()
        return account


class User(AbstractUser):

    id          = models.CharField(max_length=255, unique=True, primary_key=True,  editable=False)
    username    = None
    first_name  = models.CharField(max_length=255, verbose_name='first name', blank=True, null=True)
    last_name   = models.CharField(max_length=255, verbose_name='last name', blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    email       = models.EmailField(max_length=255, verbose_name='Email', unique=True)
    password    = models.CharField(max_length=255, verbose_name='password')
    phone_number = models.CharField(max_length=255, blank=True, null=True, unique=False)
    code        = models.CharField(max_length=255, blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    

    class Meta:
        db_table            = 'users'
        verbose_name        = 'user'
        verbose_name_plural = 'users'