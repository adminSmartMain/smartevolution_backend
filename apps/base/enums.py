from enum import Enum

class Event(Enum):
    ACUSE_RECIBO = {
        'id': "07c61f28-83f8-4f91-b965-f685f86cf6bf",
        'code': "030",
        'description': "Acuse de recibo de la Factura Electrónica de Venta"
    }
    RECIBO_BIEN_SERVICIO = {
        'id': "141db270-23ec-49c1-87a7-352d5413d309",
        'code': "032",
        'description': "Recibo del bien o prestación del servicio"
    }
    ACEPTACION_EXPRESA = {
        'id': "c508eeb3-e0e8-48e8-a26f-5295f95c1f1f",
        'code': "033",
        'description': "Aceptación expresa de la Factura Electrónica de Venta"
    }
    PRIMERA_INSCRIPCION = {
        'id': "b8d4f8d3-aded-4b1f-873e-46c89a2538ed",
        'code': "036",
        'description': "Primera inscripción de la Factura Electrónica de Venta como Título Valor en el RADIAN para negociación general"
    }
    ENDOSO_ELECTRONICO = {
        'id': "3ea77762-7208-457a-b035-70069ee42b5e",
        'code': "037",
        'description': "Endoso electrónico en propiedad con responsabilidad"
    }
    ENDOSO_GARANTIA = {
        'id': '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6',
        'code': "038",
        'description': "Endoso en garantía"
    }
    INFORME_PAGO = {
        'id': "f5d475c0-4433-422f-b3d2-7964ea0aa5c4",
        'code': "046",
        'description': "Informe para el pago de la Factura Electrónica de Venta como Título Valor"
    }
    ENDOSO_CESION = {
        'id': "3bb86c74-1d1c-4986-a905-a47624b09322",
        'code': "047",
        'description': "Endoso con efectos de cesión ordinaria"
    }



class TypeBill(Enum):
    FV = {
        "id": "fdb5feb4-24e9-41fc-9689-31aff60b76c9",
        "description": "FV"
    }
    FV_TV = {
        "id": "a7c70741-8c1a-4485-8ed4-5297e54a978a",
        "description": "FV-TV"
    }
    ENDOSADA = {
        "id": "29113618-6ab8-4633-aa8e-b3d6f242e8a4",
    }
