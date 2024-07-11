from enum import Enum


class ReceiptStatusEnum(Enum):
    PARCIAL_ANTICIPADO   = 'edd99cf7-6f47-4c82-a4fd-f13b4c60a0c0'
    PARCIAL_VENCIDO      = 'ed85d2bc-1a4b-45ae-b2fd-f931527d9f7f'
    PARCIAL_VIGENTE      = 'd40e91b1-fb6c-4c61-9da8-78d4f258181d'
    CANCELADO_ANTICIPADO = '3d461dea-0545-4a92-a847-31b8327bf033'
    CANCELADO_VENCIDO    = '62b0ca1e-f999-4a76-a07f-be1fe4f38cfb'
    CANCELADO_VIGENTE    = 'db1d1fa4-e467-4fde-9aee-bbf4008d688b'
    RECOMPRA             = 'ea8518e8-168a-46d7-b56a-1286bf0037cd'
    CANCELED_STATUSES    = ['3d461dea-0545-4a92-a847-31b8327bf033', '62b0ca1e-f999-4a76-a07f-be1fe4f38cfb', 'db1d1fa4-e467-4fde-9aee-bbf4008d688b']