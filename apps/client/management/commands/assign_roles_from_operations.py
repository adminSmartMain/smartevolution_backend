import uuid
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.client.api.models.client.index import Client, ClientRole, ClientRoleAssignment
from apps.operation.api.models.preOperation.index import PreOperation


ROLE_FIELDS = {
    "Emisor": "emitter_id",
    "Pagador": "payer_id",
    "Inversionista": "investor_id",
}

AUTO_NOTE = "Rol asignado automáticamente a partir del historial de operaciones."


class Command(BaseCommand):
    help = (
        "Asigna roles de cliente según su participación histórica en la tabla operation. "
        "Un cliente puede recibir Emisor, Pagador e Inversionista simultáneamente."
    )

    def add_arguments(self, parser):
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument(
            "--client-id",
            type=str,
            help="Procesa únicamente un cliente específico.",
        )
        scope.add_argument(
            "--limit",
            type=int,
            help="Procesa los primeros N clientes detectados en operaciones.",
        )
        scope.add_argument(
            "--all",
            action="store_true",
            help="Procesa todos los clientes detectados en operaciones.",
        )

        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persiste los cambios. Sin esta opción el comando funciona como dry-run.",
        )
        parser.add_argument(
            "--only-active-operations",
            action="store_true",
            help=(
                "Considera únicamente registros de operation con state=True. "
                "Por defecto se usa todo el historial, incluidos registros inactivos."
            ),
        )

    def handle(self, *args, **options):
        limit = options.get("limit")
        client_id = options.get("client_id")
        apply_changes = options.get("apply", False)
        only_active_operations = options.get("only_active_operations", False)

        if limit is not None and limit <= 0:
            raise CommandError("--limit debe ser mayor que 0.")

        roles = self._load_roles()
        inferred = self._infer_roles(only_active_operations=only_active_operations)

        if client_id:
            if not Client.objects.filter(id=client_id).exists():
                raise CommandError(f"No existe un cliente con id={client_id}")
            inferred = {client_id: inferred.get(client_id, set())}
        else:
            ordered_client_ids = sorted(inferred.keys())
            if limit is not None:
                ordered_client_ids = ordered_client_ids[:limit]
            inferred = {cid: inferred[cid] for cid in ordered_client_ids}

        if not inferred:
            self.stdout.write(self.style.WARNING("No se encontraron clientes para procesar."))
            return

        selected_client_ids = list(inferred.keys())
        existing_pairs = set(
            ClientRoleAssignment.objects.filter(client_id__in=selected_client_ids)
            .values_list("client_id", "role_id")
        )

        to_create = []
        already_present = 0
        clients_without_detected_roles = 0
        role_combo_counts = defaultdict(int)

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Roles inferidos desde operation"))
        self.stdout.write(
            f"Fuente: {'solo operation.state=True' if only_active_operations else 'todo el historial de operation'}"
        )
        self.stdout.write(
            f"Modo: {'APLICAR CAMBIOS' if apply_changes else 'DRY-RUN (no modifica la BD)'}"
        )
        self.stdout.write(f"Clientes seleccionados: {len(selected_client_ids)}")
        self.stdout.write("")

        for cid in selected_client_ids:
            inferred_role_names = inferred[cid]

            if not inferred_role_names:
                clients_without_detected_roles += 1
                self.stdout.write(
                    self.style.WARNING(f"{cid}: sin participación detectada en operation")
                )
                continue

            role_combo_counts[tuple(sorted(inferred_role_names))] += 1
            missing_for_client = []
            existing_for_client = []

            for role_name in sorted(inferred_role_names):
                role = roles[role_name]
                pair = (cid, role.id)
                if pair in existing_pairs:
                    already_present += 1
                    existing_for_client.append(role_name)
                    continue

                to_create.append(
                    ClientRoleAssignment(
                        id=str(uuid.uuid4()),
                        client_id=cid,
                        role_id=role.id,
                        notes=AUTO_NOTE,
                    )
                )
                missing_for_client.append(role_name)

            detected = ", ".join(sorted(inferred_role_names))
            new_text = ", ".join(missing_for_client) if missing_for_client else "ninguno"
            old_text = ", ".join(existing_for_client) if existing_for_client else "ninguno"
            self.stdout.write(
                f"{cid} | detectados=[{detected}] | nuevos=[{new_text}] | ya_existían=[{old_text}]"
            )

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Resumen"))
        self.stdout.write(f"Clientes procesados: {len(selected_client_ids)}")
        self.stdout.write(f"Asignaciones nuevas detectadas: {len(to_create)}")
        self.stdout.write(f"Asignaciones que ya existían: {already_present}")
        self.stdout.write(f"Clientes sin roles detectados: {clients_without_detected_roles}")

        for combo, count in sorted(role_combo_counts.items(), key=lambda item: (-item[1], item[0])):
            self.stdout.write(f"  {count} cliente(s): {' + '.join(combo)}")

        if not apply_changes:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "DRY-RUN finalizado. No se modificó la base de datos. "
                    "Agrega --apply cuando hayas revisado el resultado."
                )
            )
            return

        if not to_create:
            self.stdout.write(self.style.SUCCESS("No hay asignaciones nuevas por crear."))
            return

        with transaction.atomic():
            ClientRoleAssignment.objects.bulk_create(to_create, batch_size=500)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Se crearon {len(to_create)} asignaciones de rol correctamente.")
        )

    def _load_roles(self):
        roles = {}
        missing = []

        for role_name in ROLE_FIELDS:
            matches = list(ClientRole.objects.filter(name__iexact=role_name, state=1)[:2])
            if not matches:
                missing.append(role_name)
                continue
            if len(matches) > 1:
                raise CommandError(
                    f"Hay más de un rol activo llamado '{role_name}'. Corrige el catálogo antes de continuar."
                )
            roles[role_name] = matches[0]

        if missing:
            raise CommandError(
                "Faltan roles activos en clientRoles: " + ", ".join(missing)
            )

        return roles

    def _infer_roles(self, only_active_operations=False):
        inferred = defaultdict(set)
        base_qs = PreOperation.objects.all()
        if only_active_operations:
            base_qs = base_qs.filter(state=True)

        for role_name, field_name in ROLE_FIELDS.items():
            client_ids = (
                base_qs.exclude(**{f"{field_name}__isnull": True})
                .values_list(field_name, flat=True)
                .distinct()
            )
            for cid in client_ids.iterator(chunk_size=2000):
                inferred[str(cid)].add(role_name)

        return dict(inferred)
