from django.db import models

class BaseModel(models.Model):
    id              = models.CharField(max_length=255, unique=True, primary_key=True, editable=False)
    state           = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(null=True, default=None)
    user_created_at = models.ForeignKey(
    'authentication.User', on_delete=models.CASCADE, related_name='%(class)s_created_at', null=True, default=None)
    user_updated_at = models.ForeignKey(
    'authentication.User', on_delete=models.CASCADE, related_name='%(class)s_updated_at', null=True, default=None)

    class Meta:
        abstract = True