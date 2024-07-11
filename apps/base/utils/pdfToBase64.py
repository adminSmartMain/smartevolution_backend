import subprocess
import json
import PyPDF2
import base64
from io import BytesIO
from apps.base.utils.index import sendEmail


def pdfToBase64(html):
    # run node script
    process        = subprocess.Popen(['node', 'apps/base/scripts/pdf_parser/index.js',html], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    # get the data
    stdout, stderr = process.communicate()
    #parse response
    response       = json.loads(stdout.decode('utf-8'))
    #sendEmail('recuperar contraseña', str(response) , 'ander.er985@gmail.com',)
    # convert pdf to base64
    pdfBytes       = base64.b64decode(response['pdf'])
    # get number of pages
    pdfFile        = BytesIO(pdfBytes)
    pdfReader      = PyPDF2.PdfReader(pdfFile)
    numPages       = len(pdfReader.pages)
    return {
        'pdf'  : response['pdf'],
        'pages': numPages,
    }

