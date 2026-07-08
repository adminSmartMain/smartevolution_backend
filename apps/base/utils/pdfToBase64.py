import subprocess
import json
import PyPDF2
import base64
from io import BytesIO


def pdfToBase64(html):
    if isinstance(html, dict):
        input_data = json.dumps(html)
    else:
        input_data = html

    process = subprocess.Popen(
        ['node', 'apps/base/scripts/pdf_parser/index.js'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate(input=input_data.encode('utf-8'))

    stdout_text = stdout.decode('utf-8', errors='replace').strip()
    stderr_text = stderr.decode('utf-8', errors='replace').strip()

    if process.returncode != 0:
        raise Exception(
            f"Node terminó con código {process.returncode}. STDERR: {stderr_text}. STDOUT: {stdout_text}"
        )

    try:
        response = json.loads(stdout_text)
    except Exception:
        raise Exception(
            f"Node no devolvió JSON válido. STDERR: {stderr_text}. STDOUT: {stdout_text}"
        )

    if response.get('status') != 'success' or 'pdf' not in response:
        raise Exception(
            f"Puppeteer no generó PDF. Respuesta Node: {response}. STDERR: {stderr_text}"
        )

    pdfBytes = base64.b64decode(response['pdf'])
    pdfFile = BytesIO(pdfBytes)
    pdfReader = PyPDF2.PdfReader(pdfFile)

    return {
        'pdf': response['pdf'],
        'pages': len(pdfReader.pages),
    }