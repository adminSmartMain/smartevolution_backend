from django.core.management.base import BaseCommand, CommandError

from apps.client.api.models.client.index import Client
from apps.client.services.role_assignment import (
    RoleSyncError,
    apply_role_sync,
    build_role_sync_plan,
)


class Command(BaseCommand):
    help = (
        "Asigna roles de cliente según su participación histórica en la tabla operation. "
        "Un cliente puede recibir Emisor, Pagador e Inversionista simultáneamente."
    )

    def add_arguments(self, parser):
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument("--client-id", type=str, help="Procesa únicamente un cliente específico.")
        scope.add_argument("--limit", type=int, help="Procesa los primeros N clientes detectados en operaciones.")
        scope.add_argument("--all", action="store_true", help="Procesa todos los clientes detectados en operaciones.")
        parser.add_argument("--apply", action="store_true", help="Persiste los cambios. Sin esta opción funciona como dry-run.")
        parser.add_argument(
            "--only-active-operations",
            action="store_true",
            help="Considera únicamente operation.state=True. Por defecto usa todo el historial.",
        )

    def handle(self, *args, **options):
        client_id = options.get("client_id")
        limit = options.get("limit")
        apply_changes = options.get("apply", False)
        only_active_operations = options.get("only_active_operations", False)

        if client_id and not Client.objects.filter(id=client_id).exists():
            raise CommandError(f"No existe un cliente con id={client_id}")

        try:
            plan = build_role_sync_plan(
                client_ids=[client_id] if client_id else None,
                limit=limit,
                only_active_operations=only_active_operations,
            )
        except RoleSyncError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Roles inferidos desde operation"))
        self.stdout.write(
            f"Fuente: {'solo operation.state=True' if only_active_operations else 'todo el historial de operation'}"
        )
        self.stdout.write(f"Modo: {'APLICAR CAMBIOS' if apply_changes else 'DRY-RUN (no modifica la BD)'}")
        self.stdout.write(f"Clientes seleccionados: {len(plan['selected_client_ids'])}")
        self.stdout.write("")

        for row in plan["client_rows"]:
            detected = ", ".join(row["detected"]) or "ninguno"
            new_text = ", ".join(row["new"]) or "ninguno"
            reactivate_text = ", ".join(row["reactivate"]) or "ninguno"
            existing_text = ", ".join(row["existing"]) or "ninguno"
            self.stdout.write(
                f"{row['client_id']} | detectados=[{detected}] | nuevos=[{new_text}] | "
                f"reactivar=[{reactivate_text}] | ya_existían=[{existing_text}]"
            )

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Resumen"))
        self.stdout.write(f"Clientes procesados: {len(plan['selected_client_ids'])}")
        self.stdout.write(f"Asignaciones nuevas/reactivadas: {plan['new_assignments']}")
        self.stdout.write(f"Asignaciones activas ya existentes: {plan['already_active']}")
        self.stdout.write(f"Clientes sin roles detectados: {plan['clients_without_detected_roles']}")
        for role_name, count in plan["role_new_counts"].items():
            self.stdout.write(f"  {role_name}: {count} por crear/reactivar")

        if not apply_changes:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("DRY-RUN finalizado. No se modificó la base de datos."))
            return

        result = apply_role_sync(plan)
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Sincronización completada: {result['created']} creadas, "
                f"{result['reactivated']} reactivadas."
            )
        )
