from drf_extra_fields.fields import Base64FileField
from apps.base.exceptions import HttpException

class XMLBase64File(Base64FileField):
    ALLOWED_TYPES = ['pdf','csv', 'xls', 'xlsx','xml']

    def get_file_extension(self, filename, decoded_file):
        return 'xml'