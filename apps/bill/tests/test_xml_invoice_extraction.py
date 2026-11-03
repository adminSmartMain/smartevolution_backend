from base64 import b64encode

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.base.utils.index import gen_uuid
from apps.bill.utils.xml_upload import decode_xml_invoice_payload


def xml_data_uri(content, media_type='text/xml'):
    encoded = b64encode(content).decode('ascii')
    return f'data:{media_type};base64,{encoded}'


class XmlInvoicePayloadTests(APITestCase):
    def test_accepts_well_formed_text_xml(self):
        payload = xml_data_uri(b'<?xml version="1.0"?><Invoice />')

        xml_bytes, normalized = decode_xml_invoice_payload(payload)

        self.assertEqual(xml_bytes, b'<?xml version="1.0"?><Invoice />')
        self.assertEqual(normalized, payload)

    def test_accepts_well_formed_application_xml(self):
        payload = xml_data_uri(b'<Invoice><ID>INV-1</ID></Invoice>', 'application/xml')

        _, normalized = decode_xml_invoice_payload(payload)

        self.assertTrue(normalized.startswith('data:text/xml;base64,'))

    def test_rejects_pdf_even_when_its_content_is_base64(self):
        payload = xml_data_uri(b'%PDF-1.7', 'application/pdf')

        with self.assertRaisesRegex(ValueError, 'Solo se permiten archivos XML'):
            decode_xml_invoice_payload(payload)

    def test_rejects_malformed_xml(self):
        payload = xml_data_uri(b'<Invoice><ID>INV-1</Invoice>')

        with self.assertRaisesRegex(ValueError, 'no contiene un XML válido'):
            decode_xml_invoice_payload(payload)

    def test_rejects_invalid_base64(self):
        with self.assertRaisesRegex(ValueError, 'no está codificado correctamente'):
            decode_xml_invoice_payload('data:text/xml;base64,not-valid-base64!')


class XmlInvoiceExtractionEndpointTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model(
            id=gen_uuid(),
            email='xml-extraction-admin@local.invalid',
            first_name='XML',
            last_name='Admin',
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        self.user.set_password('SecurePass_123!')
        self.user.save()
        self.client.force_authenticate(self.user)

    def test_endpoint_reports_non_xml_as_failed_without_extracting_it(self):
        response = self.client.post(
            '/api/bill/read',
            {'bills': [xml_data_uri(b'%PDF-1.7', 'application/pdf')]},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['bills'], [])
        self.assertEqual(len(response.data['failedBills']), 1)
        self.assertEqual(
            response.data['failedBills'][0]['message'],
            'Solo se permiten archivos XML para extraer facturas',
        )

    def test_endpoint_reports_malformed_xml_as_failed_without_extracting_it(self):
        response = self.client.post(
            '/api/bill/read',
            {'bills': [xml_data_uri(b'<Invoice><ID>INV-1</Invoice>')]},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['bills'], [])
        self.assertEqual(
            response.data['failedBills'][0]['message'],
            'El archivo no contiene un XML válido',
        )
