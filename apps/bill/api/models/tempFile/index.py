from django.db import models


class tempFile(models.Model):
    bill = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='billsFiles/', null=True, blank=True)
    class Meta:
        db_table = 'tempFile'
        ordering = ['-bill']
