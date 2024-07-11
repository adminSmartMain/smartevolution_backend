from django.db import models
from apps.base.models import BaseModel
from apps.authentication.api.models.user.index import User
from apps.authentication.api.models.role.index import Role


class UserRole(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)


    class Meta:
        db_table = 'userRoles'
        verbose_name = 'userRole'
        verbose_name_plural = 'userRoles'
        ordering = ['-created_at']

