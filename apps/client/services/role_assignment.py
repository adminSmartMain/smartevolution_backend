import uuid
from collections import defaultdict

from django.db import transaction

from apps.client.api.models.client.index import Client, ClientRole, ClientRoleAssignment
from apps.operation.api.models.preOperation.index import PreOperation


ROLE_FIELDS = {
    "Emisor": "emitter_id",
    "Pagador": "payer_id",
    "Inversionista": "investor_id",
}

AUTO_NOTE = "Rol asignado automáticamente a partir del historial de operaciones."


class RoleSyncError(Exception):
    """Error de validación de la sincronización de roles."""


def _load_roles():
    roles = {}
    missing = []

    for role_name in ROLE_FIELDS:
        matches = list(ClientRole.objects.filter(name__iexact=role_name, state=1)[:2])
        if not matches:
            missing.append(role_name)
            continue
        if len(matches) > 1:
            raise RoleSyncError(
                f"Hay más de un rol activo llamado '{role_name}'. "
                "Corrige el catálogo antes de continuar."
            )
        roles[role_name] = matches[0]

    if missing:
        raise RoleSyncError(
            "Faltan roles activos en clientRoles: " + ", ".join(missing)
        )

    return roles


def _infer_roles(only_active_operations=False):
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
        for client_id in client_ids.iterator(chunk_size=2000):
            inferred[str(client_id)].add(role_name)

    return dict(inferred)


def build_role_sync_plan(client_ids=None, limit=None, only_active_operations=False):
    """
    Construye un preview sin modificar la base de datos.

    La regla es histórica por defecto: si un cliente apareció alguna vez como
    emisor, pagador o inversionista en operation, debe tener ese rol.
    """
    if limit is not None and limit <= 0:
        raise RoleSyncError("El límite debe ser mayor que 0.")

    roles = _load_roles()
    inferred = _infer_roles(only_active_operations=only_active_operations)

    if client_ids is not None:
        requested_ids = [str(client_id) for client_id in client_ids]
        existing_client_ids = set(
            str(value)
            for value in Client.objects.filter(id__in=requested_ids).values_list("id", flat=True)
        )
        inferred = {
            client_id: inferred.get(client_id, set())
            for client_id in requested_ids
            if client_id in existing_client_ids
        }
    else:
        ordered_ids = sorted(inferred.keys())
        if limit is not None:
            ordered_ids = ordered_ids[:limit]
        inferred = {client_id: inferred[client_id] for client_id in ordered_ids}

    selected_client_ids = list(inferred.keys())

    existing_assignments = {
        (str(assignment.client_id), str(assignment.role_id)): assignment
        for assignment in ClientRoleAssignment.objects.filter(
            client_id__in=selected_client_ids
        )
    }

    to_create = []
    to_reactivate = []
    already_active = 0
    clients_without_detected_roles = 0
    role_new_counts = {role_name: 0 for role_name in ROLE_FIELDS}
    role_detected_counts = {role_name: 0 for role_name in ROLE_FIELDS}

    client_rows = []

    for client_id in selected_client_ids:
        inferred_role_names = inferred[client_id]
        if not inferred_role_names:
            clients_without_detected_roles += 1

        row = {
            "client_id": client_id,
            "detected": sorted(inferred_role_names),
            "new": [],
            "reactivate": [],
            "existing": [],
        }

        for role_name in sorted(inferred_role_names):
            role_detected_counts[role_name] += 1
            role = roles[role_name]
            pair = (str(client_id), str(role.id))
            assignment = existing_assignments.get(pair)

            if assignment is None:
                to_create.append(
                    ClientRoleAssignment(
                        id=str(uuid.uuid4()),
                        client_id=client_id,
                        role_id=role.id,
                        notes=AUTO_NOTE,
                    )
                )
                row["new"].append(role_name)
                role_new_counts[role_name] += 1
            elif not assignment.state:
                to_reactivate.append(assignment)
                row["reactivate"].append(role_name)
                role_new_counts[role_name] += 1
            else:
                already_active += 1
                row["existing"].append(role_name)

        client_rows.append(row)

    total_active_clients = Client.objects.filter(state=True).count()
    clients_with_active_role = (
        ClientRoleAssignment.objects.filter(state=True, client__state=True, role__state=1)
        .values("client_id")
        .distinct()
        .count()
    )

    return {
        "roles": roles,
        "selected_client_ids": selected_client_ids,
        "client_rows": client_rows,
        "to_create": to_create,
        "to_reactivate": to_reactivate,
        "already_active": already_active,
        "clients_without_detected_roles": clients_without_detected_roles,
        "role_new_counts": role_new_counts,
        "role_detected_counts": role_detected_counts,
        "total_active_clients": total_active_clients,
        "clients_with_active_role": clients_with_active_role,
        "clients_without_active_role": max(total_active_clients - clients_with_active_role, 0),
        "new_assignments": len(to_create) + len(to_reactivate),
        "only_active_operations": only_active_operations,
    }


def apply_role_sync(plan, user=None):
    """Aplica un plan previamente construido y devuelve el resumen final."""
    to_create = plan["to_create"]
    to_reactivate = plan["to_reactivate"]

    with transaction.atomic():
        if to_create:
            if user is not None:
                for assignment in to_create:
                    assignment.user_created_at = user
            ClientRoleAssignment.objects.bulk_create(to_create, batch_size=500)

        if to_reactivate:
            for assignment in to_reactivate:
                assignment.state = True
                assignment.notes = AUTO_NOTE
                if user is not None:
                    assignment.user_updated_at = user
            ClientRoleAssignment.objects.bulk_update(
                to_reactivate,
                ["state", "notes", "user_updated_at"],
                batch_size=500,
            )

    return {
        "created": len(to_create),
        "reactivated": len(to_reactivate),
        "total_applied": len(to_create) + len(to_reactivate),
        "already_active": plan["already_active"],
        "clients_processed": len(plan["selected_client_ids"]),
        "role_new_counts": plan["role_new_counts"],
    }
