import csv
from pathlib import Path
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.bill.models import Bill
from apps.authentication.models import User
from apps.client.models import Account, Broker, Client, RiskProfile
from apps.misc.models import TypeBill, TypeOperation
from apps.operation.models import PreOperation


NULL_VALUES = {'', 'NULL', 'None', None}


def normalize(value):
    return None if value in NULL_VALUES else value


def load_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source))


def model_values(model, row, *, keep_id=True):
    allowed = {field.attname for field in model._meta.fields}
    values = {
        name: normalize(value)
        for name, value in row.items()
        if name in allowed and (keep_id or name != 'id')
    }
    for field in model._meta.fields:
        if field.get_internal_type() == 'BooleanField' and values.get(field.attname) is not None:
            values[field.attname] = str(values[field.attname]).lower() in {'1', 'true'}
    # Audit actors are not part of the financial relationship graph. Preserve
    # them when available locally, but do not let a historic missing user make
    # an otherwise valid test fixture impossible to import.
    for name in ('user_created_at_id', 'user_updated_at_id', 'user_id', 'watchlistActivatedBy_id'):
        if values.get(name) and not User.objects.filter(pk=values[name]).exists():
            values[name] = None
    return values


class Command(BaseCommand):
    help = 'Imports a complete operation snapshot safely into the local database.'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=Path)

    def handle(self, *args, **options):
        directory = options['directory']
        files = {
            'operations': directory / 'aaa.csv',
            'bills': directory / 'bbbb.csv',
            'clients': directory / 'cccc.csv',
            'accounts': directory / 'dddd.csv',
            'brokers': directory / 'eeee.csv',
            'type_operation': directory / 'i.csv',
            'type_bill': directory / 'jj.csv',
            'risk_profile': directory / 'kkk.csv',
        }
        absent = [str(path) for path in files.values() if not path.is_file()]
        if absent:
            raise CommandError(f'Faltan archivos requeridos: {", ".join(absent)}')

        rows = {name: load_rows(path) for name, path in files.items()}
        source_op_ids = {row['opId'] for row in rows['operations']}
        if len(source_op_ids) != 1:
            raise CommandError('El snapshot debe contener exactamente un opId de origen.')

        with transaction.atomic():
            last_operation = PreOperation.objects.select_for_update().order_by('-opId').first()
            target_op_id = (last_operation.opId if last_operation else 0) + 1

            # These are reference records. Existing local rows are never
            # overwritten; missing rows are copied with their original IDs.
            for model, key in (
                (Broker, 'brokers'),
                (TypeOperation, 'type_operation'),
                (TypeBill, 'type_bill'),
                (Client, 'clients'),
                (Account, 'accounts'),
                (Bill, 'bills'),
                (RiskProfile, 'risk_profile'),
            ):
                for row in rows[key]:
                    values = model_values(model, row)
                    identifier = values.pop('id')
                    model.objects.get_or_create(pk=identifier, defaults=values)

            for row in rows['operations']:
                values = model_values(PreOperation, row, keep_id=False)
                values['id'] = str(uuid4())
                values['opId'] = target_op_id
                PreOperation.objects.create(**values)

        self.stdout.write(self.style.SUCCESS(
            f'Snapshot de operación {next(iter(source_op_ids))} importado como opId={target_op_id} '
            f'con {len(rows["operations"])} detalles.'
        ))
