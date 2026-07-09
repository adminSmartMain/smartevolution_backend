from django.db import models
from apps.base.models import BaseModel


class Role(BaseModel):
    AUDIENCE_INTERNAL = 'INTERNAL'
    AUDIENCE_CLIENT = 'CLIENT_PORTAL'
    AUDIENCE_CHOICES = ((AUDIENCE_INTERNAL, 'Internal'), (AUDIENCE_CLIENT, 'Client portal'))
    code = models.CharField(max_length=80, unique=True, null=True, blank=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    description = models.TextField(blank=False, null=False)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default=AUDIENCE_INTERNAL)
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return self.name or self.description

    class Meta:
        db_table = 'roles'
        verbose_name = 'role'
        verbose_name_plural = 'roles'
        ordering = ['-created_at']


class Permission(BaseModel):
    code = models.CharField(max_length=120, unique=True)
    module = models.CharField(max_length=80)
    action = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'permissions'
        ordering = ['module', 'action']

    def __str__(self):
        return self.code


class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permission_assignments')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_assignments')

    class Meta:
        db_table = 'role_permissions'
        constraints = [models.UniqueConstraint(fields=['role', 'permission'], name='uniq_role_permission')]


class AccessAudit(models.Model):
    id = models.CharField(max_length=255, primary_key=True, editable=False)
    actor = models.ForeignKey('authentication.User', null=True, on_delete=models.SET_NULL, related_name='access_audits')
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=255, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'access_audit'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['target_type','target_id'], name='idx_audit_target'), models.Index(fields=['created_at'], name='idx_audit_created')]
