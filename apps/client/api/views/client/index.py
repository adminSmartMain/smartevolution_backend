# REST Framework imports
from django.db.models import Q 
from django.db import IntegrityError
# Models
from apps.client.models import Client, Account
# Serializers
from apps.client.api.serializers.index import ClientSerializer, ClientReadOnlySerializer, ClientByIdSerializer,LegalRepresentativeSerializer, ContactSerializer
from apps.authentication.api.serializers.index import UserSerializer
# Utils
from apps.base.utils.index import response, BaseAV
from apps.client.utils.index import createClient, saveContacts, saveLegalRepresentative, createAccount, genRequest
# Decorators
from apps.base.decorators.index import checkRole
from apps.client.api.models.client.index import ClientRole, ClientRoleAssignment
from apps.client.api.serializers.client.index import ClientRoleAssignmentSerializer, ClientRoleSerializer
from rest_framework import viewsets
from rest_framework.decorators import APIView
from django.db.models import OuterRef, Subquery, DateTimeField, IntegerField, Count, Value
from django.db.models.functions import Coalesce
from apps.client.api.models.client.index import Client 
from apps.client.api.models.account.index import Account
from apps.operation.api.models.preOperation.index import PreOperation as Operation
from apps.bill.api.models.bill.index import Bill
import uuid
from django.db.models import (
    Q, OuterRef, Subquery, DateTimeField, IntegerField, Count, Value,
    Sum, Case, When, F, DecimalField, Exists
)
from django.db.models.functions import Coalesce
from django.db import models
from rest_framework.response import Response
def gen_uuid():
    return uuid.uuid4()
def normalize_role_ids(value):
    """
    Acepta:
      - None
      - "uuid"
      - ["uuid1","uuid2"]
    Retorna lista limpia sin duplicados.
    """
    if not value:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        # limpia nulos, strings vacíos y dupes
        out = []
        seen = set()
        for x in value:
            if not x:
                continue
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    return []

class ClientAV(BaseAV):
    @checkRole(['admin'])
   
    def get(self, request, pk=None):
        try:
            clients_qs = Client.objects.filter(state=1)

            # =========================
            # SUBQUERIES
            # =========================

            # 1) RegisteredAt = created_at de la cuenta (más antigua)
            account_created_sq = (
                Account.objects
                .filter(client_id=OuterRef("pk"))
                .order_by("created_at")
                .values("created_at")[:1]
            )

            # 2) SaldoCuenta = balance de la cuenta más antigua
            saldo_cuenta_sq = (
                Account.objects
                .filter(client_id=OuterRef("pk"))
                .order_by("created_at")
                .values("balance")[:1]
            )

            # 3) LastOperationAt = última operación donde participe en cualquier rol
            last_op_sq = (
                Operation.objects
                .filter(
                    Q(emitter_id=OuterRef("pk")) |
                    Q(payer_id=OuterRef("pk")) |
                    Q(investor_id=OuterRef("pk"))
                )
                .order_by("-created_at")
                .values("created_at")[:1]
            )

            # 4) InvoicesTotal = total bills donde emitterId = document_number
            invoices_total_sq = (
                Bill.objects
                .filter(emitterId=OuterRef("document_number"))
                .values("emitterId")
                .annotate(c=Count("id"))
                .values("c")[:1]
            )

            # 5) InvoicesPending = bills del cliente que tienen al menos 1 preoperación
            # ✅ Optimizado: join directo usando el related_name real -> preOperationsBill
            invoices_pending_sq = (
                Bill.objects
                .filter(emitterId=OuterRef("document_number"), preOperationsBill__isnull=False)
                .values("emitterId")
                .annotate(c=Count("id", distinct=True))
                .values("c")[:1]
            )

            # 6) PorCobrar = SUM(opPendingAmount) de operaciones donde el cliente participe
            # ✅ Optimizado: sin agrupar por emitter_id
            por_cobrar_sq = (
                Operation.objects
                .filter(
                    Q(emitter_id=OuterRef("pk")) |
                    Q(payer_id=OuterRef("pk")) |
                    Q(investor_id=OuterRef("pk"))
                )
                .values()  # sin GROUP BY
                .annotate(s=Coalesce(Sum("opPendingAmount"), Value(0.0)))
                .values("s")[:1]
            )

            # 7) IsInvestor (más rápido que Count)
            is_investor_sq = Exists(
                ClientRoleAssignment.objects.filter(
                    client_id=OuterRef("pk"),
                    role__name__iexact="Inversionista"
                )
            )

            money_field = DecimalField(max_digits=20, decimal_places=2)

            # =========================
            # ANNOTATES
            # =========================
            clients_qs = clients_qs.annotate(
                RegisteredAt=Subquery(account_created_sq, output_field=DateTimeField()),
                LastOperationAt=Subquery(last_op_sq, output_field=DateTimeField()),

                InvoicesTotal=Coalesce(Subquery(invoices_total_sq, output_field=IntegerField()), Value(0)),
                InvoicesPending=Coalesce(Subquery(invoices_pending_sq, output_field=IntegerField()), Value(0)),

                SaldoCuenta=Coalesce(
                    Subquery(saldo_cuenta_sq, output_field=money_field),
                    Value(0, output_field=money_field),
                ),
                PorCobrar=Coalesce(
                    Subquery(por_cobrar_sq, output_field=money_field),
                    Value(0, output_field=money_field),
                ),

                IsInvestor=is_investor_sq,
            ).annotate(
                TotalPortafolio=Case(
                    When(IsInvestor=True, then=F("PorCobrar") + F("SaldoCuenta")),
                    default=F("PorCobrar"),
                    output_field=money_field,
                )
            )

            # =========================
            # FILTROS
            # =========================
            q_client = request.query_params.get("client")
            if q_client:
                clients_qs = clients_qs.filter(
                    Q(social_reason__icontains=q_client) |
                    Q(first_name__icontains=q_client) |
                    Q(last_name__icontains=q_client)
                )

            q_intel = request.query_params.get("intelligent_query")
            if q_intel:
                clients_qs = clients_qs.filter(
                    Q(social_reason__icontains=q_intel) |
                    Q(first_name__icontains=q_intel) |
                    Q(last_name__icontains=q_intel) |
                    Q(document_number__icontains=q_intel)
                )

            q_doc = request.query_params.get("document")
            if q_doc:
                clients_qs = clients_qs.filter(document_number__icontains=q_doc)

            # =========================
            # PK / LIST
            # =========================
            if pk:
                if pk == "all":
                    serializer = ClientSerializer(clients_qs, many=True)
                    return Response({"error": False, "data": serializer.data}, status=200)

                client = clients_qs.filter(id=pk).first()
                if not client:
                    return Response({"error": True, "message": "Clientes no encontrados"}, status=404)

                serializer = ClientByIdSerializer(client)
                return Response({"error": False, "data": serializer.data}, status=200)

            page = self.paginate_queryset(clients_qs)
            if page is not None:
                serializer = ClientReadOnlySerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = ClientReadOnlySerializer(clients_qs, many=True)
            return Response({"error": False, "data": serializer.data}, status=200)

        except Exception as e:
            import traceback
            traceback.print_exc()

        
    @checkRole(['admin'])
    def post(self, request):
        try:
            # ✅ Validación de email (tu lógica)
            if request.data.get('type_client') == 'e646e875-c07f-420e-90e5-cae468587c05':
                if Client.objects.filter(email=request.data.get('email')).exists():
                    return response({'error': True, 'message': 'Ya existe un usuario con este email'}, 400)

            getUser = None
            request.data['entered_by'] = request.user.id
            request.data['user'] = getUser

            # 1) Crear cliente (tu lógica)
            client = createClient(request, getUser)  # puede retornar dict o instancia

            # 2) Guardar lo demás
            saveContacts(request, client, getUser)
            saveLegalRepresentative(request, client, getUser)
            createAccount(request, client, getUser)

            # ============================
            # ✅ ROLES MÚLTIPLES
            # ============================
            role_ids = normalize_role_ids(request.data.get("rol_client"))

            if role_ids:
                # 1) Validación: que existan y estén activos
                valid_count = ClientRole.objects.filter(id__in=role_ids, state=1).count()
                if valid_count != len(role_ids):
                    return response({"error": True, "message": "Uno o más roles no existen"}, 400)

                client_id = client.get("id") if isinstance(client, dict) else client.id
                notes = request.data.get("role_notes", "")

                # 2) Roles ya asignados (por si reintentan o hay duplicados previos)
                existing = set(
                    ClientRoleAssignment.objects.filter(client_id=client_id, role_id__in=role_ids)
                    .values_list("role_id", flat=True)
                )

                # 3) Crear solo los que faltan
                to_create = [
                    ClientRoleAssignment( id=gen_uuid(), client_id=client_id, role_id=rid, notes=notes)
                    for rid in role_ids
                    if rid not in existing
                ]

                # 4) Guardar (IntegrityError solo aquí)
                try:
                    if to_create:
                        ClientRoleAssignment.objects.bulk_create(to_create)
                except IntegrityError as e:
                    # ✅ Si cae aquí, SÍ es por roles (o constraint del puente)
                    return response(
                        {'error': True, 'message': 'Este cliente ya tiene asignado uno de esos roles'},
                        400
                    )

            return response({'error': False, 'message': 'cliente registrado', 'data': client}, 201)

        except Exception as e:
            # ✅ cualquier otra cosa (email duplicado, account, doc, etc) no se disfraza de "rol"
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


    @checkRole(['admin'])
    def patch(self, request, pk=None):
        try:
            client = Client.objects.get(id=pk)
            serializer = ClientSerializer(client, data=request.data, partial=True, context={'request': request})

            if serializer.is_valid():
                serializer.save()

                # ✅ SYNC ROLES (si vienen en el payload)
                if "rol_client" in request.data:
                    role_ids = normalize_role_ids(request.data.get("rol_client"))

                    # ✅ Validación: roles existentes
                    if role_ids:
                        valid_count = ClientRole.objects.filter(id__in=role_ids, state=1).count()
                        if valid_count != len(role_ids):
                            return response({"error": True, "message": "Uno o más roles no existen"}, 400)

                    # ✅ borra los que ya no están (si role_ids=[], borra todos)
                    ClientRoleAssignment.objects.filter(client=client).exclude(role_id__in=role_ids).delete()

                    # ✅ crea los nuevos que falten
                    existing = set(
                        ClientRoleAssignment.objects.filter(client=client, role_id__in=role_ids)
                        .values_list("role_id", flat=True)
                    )

                    notes = request.data.get("role_notes", "")

                    to_create = [
                        ClientRoleAssignment(
                            id=gen_uuid(),                 # ✅ IMPORTANTE si tu BaseModel usa UUID
                            client=client,
                            role_id=rid,
                            notes=notes,
                            user_created_at=request.user   # ✅ si tu BaseModel lo requiere
                        )
                        for rid in role_ids
                        if rid not in existing
                    ]

                    if to_create:
                        # ✅ evita reventar por constraint uniq_client_role_assignment
                        ClientRoleAssignment.objects.bulk_create(to_create, ignore_conflicts=True)

                # ----- tu lógica existente (sin cambios) -----
                if 'legal_representative' in request.data:
                    LegalRepresentative = LegalRepresentativeSerializer.Meta.model.objects.get(client=client)
                    lRSerializer = LegalRepresentativeSerializer(
                        LegalRepresentative,
                        data=request.data['legal_representative'],
                        partial=True,
                        context={'request': request}
                    )
                    if lRSerializer.is_valid():
                        lRSerializer.save()

                if 'contacts' in request.data:
                    contacts = ContactSerializer.Meta.model.objects.filter(client=client)
                    if len(contacts) > 0:
                        ContactSerializer.Meta.model.objects.filter(client=client).delete()

                    for x in request.data['contacts']:
                        x['client'] = client.id
                        contactSerializer = ContactSerializer(data=x, context={'request': request})
                        if contactSerializer.is_valid():
                            contactSerializer.save()

                return response({'error': False, 'data': serializer.data}, 200)

            return response({'error': True, 'message': serializer.errors}, 400)

        except Client.DoesNotExist:
            return response({'error': True, 'message': 'Cliente no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)



    @checkRole(['admin'])
    def delete(self, request, pk=None):
        try:
            client = Client.objects.get(id=pk)
            client.state = 0
            client.save()
            # disable the accounts of the client
            Account.objects.filter(client=client).update(state=0)
            return response({'error': False, 'message': 'Cliente eliminado'}, 200)
        except Client.DoesNotExist:
            return response({'error': True, 'message': 'Client no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class ClientByTermAV(BaseAV):
    @checkRole(['admin'])
    def get(self, request, term=None):
        try:
            clients = Client.objects.filter(Q(social_reason__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(document_number__icontains=term))
            serializer = ClientByIdSerializer(clients, many=True)
            return response({'error': False, 'data': serializer.data}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


    @checkRole(['admin'])
    def get(self, request):
        try:
            if request.query_params.get('client') != None:
                clients = Client.objects.filter(Q(social_reason__icontains=request.query_params.get('client')) | Q(first_name__icontains=request.query_params.get('client')) | Q(last_name__icontains=request.query_params.get('client')))
                
            if request.query_params.get('document') != None:
                clients = Client.filter(document_number__icontains=request.query_params.get('document'))

            serializer = ClientSerializer(clients, many=True)
            return response({'error': False, 'data': serializer.data}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        

class ClientRoleViewSet(APIView):
    
    
    @checkRole(['admin'])
    def get(self, request, pk=None):
        if pk:
            riskProfile = ClientRole.objects.get(pk=pk)
            serializer  = ClientRoleSerializer(riskProfile)
            return response({'error': False, 'data': serializer.data}, 200)
        else:
            riskProfile = ClientRole.objects.filter(state=1)
            serializer  = ClientRoleSerializer(riskProfile, many=True)
            return response({'error': False, 'data': serializer.data}, 200)

    @checkRole(['admin'])
    def post(self, request):
        serializer =ClientRoleSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return response({'error': False, 'data': serializer.data}, 200)
        else:
            return response({'error': True, 'message': serializer.errors}, 400)
    

class ClientRoleAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ClientRoleAssignment.objects.select_related("client", "role").all().order_by("-created_at")
    serializer_class = ClientRoleAssignmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        client_id = self.request.query_params.get("client")
        role_id = self.request.query_params.get("role")

        if client_id:
            qs = qs.filter(client_id=client_id)
        if role_id:
            qs = qs.filter(role_id=role_id)

        return qs