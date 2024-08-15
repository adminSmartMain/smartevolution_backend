from django.contrib import admin
from import_export import resources
from import_export.admin import ExportActionModelAdmin
from apps.authentication.api.models.user.index import User
from apps.authentication.api.models.role.index import Role
from apps.authentication.api.models.userRole.index import UserRole

LIST_PER_PAGE = 20

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = '__all__'
        import_id_fields = ('id',)

class RoleResource(resources.ModelResource):
    class Meta:
        model = Role
        fields = '__all__'
        import_id_fields = ('id',)

class UserRoleResource(resources.ModelResource):
    class Meta:
        model = UserRole
        fields = '__all__'
        import_id_fields = ('id',)

@admin.register(User)
class UserAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = UserResource
    list_display = ('id', 'username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'date_joined')
    list_per_page = LIST_PER_PAGE

@admin.register(Role)
class RoleAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = RoleResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)
    list_per_page = LIST_PER_PAGE

@admin.register(UserRole)
class UserRoleAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = UserRoleResource
    list_display = ('id', 'user', 'role', 'created_at')
    search_fields = ('user__username', 'role__description')
    list_filter = ('user', 'role')
    list_per_page = LIST_PER_PAGE