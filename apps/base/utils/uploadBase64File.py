from apps.base.utils.getContentInfo import get_content_info as getContentInfo
import boto3
from boto3.session import Session
from botocore.exceptions import ClientError
from base64 import b64decode
from django.conf import settings
from apps.base.exceptions import HttpException


class BucketS3():
    session = None
    def __init__(self):
        self._ini_session_s3()
    def _ini_session_s3(self):
        self.session = Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                               region_name=settings.AWS_REGION)

    def upload_file(self, file=None, file_path=None, content_type=None):
        s3 = self.session.resource('s3')
        object_data = {
            "Key": file_path,
            "Body": file,
            "ACL": 'public-read',
        }

        if content_type:
            object_data["ContentType"] = content_type

        s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME).put_object(**object_data)
        return file_path

    @staticmethod
    def get_document_link(relative_url):
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{relative_url}"


def uploadFileBase64(files_bse64=None, file_path=None):
    """
    Funcion que carga el archivo en base 64 a S3
    """
    for file in files_bse64:
        # Validamos si es un archivo PDF
        file_content = getContentInfo(file)
        #if file_content["file_format"] not in ('xml'):
         #   raise HttpException(400, "Contenido multimedia no válido para almacenar.")
        # Validamos si se proporciono el documento RUT
        bytes = b64decode(file_content["content"], validate=True)
        # Subiendo el documento a el storage de s3
        return BucketS3().upload_file(
            file=bytes,
            file_path=file_path+'.'+file_content["file_format"],
            content_type=f'image/{file_content["file_format"]}'
        )