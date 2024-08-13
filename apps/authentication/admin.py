from django.contrib import admin
from apps.authentication.api.models.user.index import User
from apps.authentication.api.models.role.index import Role
from apps.authentication.api.models.userRole.index import UserRole

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'date_joined')  # Personaliza según los campos del modelo
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'date_joined')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')  # Personaliza según los campos del modelo
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'created_at')  # Personaliza según los campos del modelo
    search_fields = ('user__username', 'role__name')  # Si "user" y "role" son ForeignKeys
    list_filter = ('user', 'role')