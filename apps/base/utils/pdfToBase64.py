import subprocess
import json
import PyPDF2
import base64
from io import BytesIO
from apps.base.utils.index import sendEmail


def pdfToBase64(html):
    process = subprocess.Popen(
        ['node', 'apps/base/scripts/pdf_parser/index.js'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate(input=html.encode('utf-8'))

    response = json.loads(stdout.decode('utf-8'))

    pdfBytes = base64.b64decode(response['pdf'])
    pdfFile  = BytesIO(pdfBytes)
    pdfReader = PyPDF2.PdfReader(pdfFile)

    return {
        'pdf': response['pdf'],
        'pages': len(pdfReader.pages),
    }


