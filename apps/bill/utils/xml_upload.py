"""Validation for XML invoice payloads received as data URIs."""

from base64 import b64decode
from binascii import Error as Base64Error
from xml.etree import ElementTree


_XML_DATA_URI_PREFIXES = (
    'data:text/xml;base64,',
    'data:application/xml;base64,',
)


def decode_xml_invoice_payload(payload):
    """Return XML bytes from an XML data URI or raise ``ValueError``.

    Invoice extraction receives files encoded by the browser.  Checking only
    the base64 content is not enough: a PDF or image can also be base64.  This
    boundary accepts the two standard XML media types and verifies that their
    decoded content is well-formed XML before the invoice parser is called.
    """
    if not isinstance(payload, str):
        raise ValueError('El archivo debe ser un XML codificado en base64')

    normalized_payload = payload.strip()
    prefix = next(
        (
            candidate
            for candidate in _XML_DATA_URI_PREFIXES
            if normalized_payload.lower().startswith(candidate)
        ),
        None,
    )
    if prefix is None:
        raise ValueError('Solo se permiten archivos XML para extraer facturas')

    encoded_xml = normalized_payload[len(prefix):]
    if not encoded_xml:
        raise ValueError('El archivo XML está vacío')

    try:
        xml_bytes = b64decode(encoded_xml, validate=True)
    except (Base64Error, ValueError):
        raise ValueError('El contenido del XML no está codificado correctamente')

    if not xml_bytes.strip():
        raise ValueError('El archivo XML está vacío')

    try:
        ElementTree.fromstring(xml_bytes)
    except (ElementTree.ParseError, ValueError, UnicodeError):
        raise ValueError('El archivo no contiene un XML válido')

    # Always persist the normalized media type expected by the existing API.
    return xml_bytes, f'data:text/xml;base64,{encoded_xml}'
