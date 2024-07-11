# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import (LegalClient, FinancialRelations, LegalClientContacts, ManagementBoard,
                                PartnersAndShareholders, PrincipalClients, PrincipalCompetitors, PrincipalProducts
                                , PrincipalProviders, NaturalClient, Contact, Client, LegalClientDocuments, NaturalClientDocuments)
from apps.authentication.api.models.user.index import User
# Serializers
from apps.authentication.api.serializers.user.index import UserSerializer
from apps.misc.api.serializers.index import CIIUReadOnlySerializer, TypeIdentitySerializer, DepartmentSerializer, CitySerializer, CountrySerializer
from apps.client.api.serializers.client.index import ClientSerializer, LegalRepresentativeSerializer, AccountSerializer, ContactSerializer
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid, PDFBase64File, random_with_N_digits, sendWhatsApp
import requests
# Exceptions
from apps.base.exceptions import HttpException

class LegalCLientSerializer(serializers.ModelSerializer):
    bankCertification = PDFBase64File()
    legalRepresentationCertification = PDFBase64File()
    financialStatementsCertification = PDFBase64File()
    rentDeclaration = PDFBase64File()
    rutFile = PDFBase64File()
    dianAccountState = PDFBase64File()
    legalRepresentativeDocumentFile = PDFBase64File()
    legalRepresentativeIdFile = PDFBase64File()
    shareholdingStructure = PDFBase64File()


    class Meta:
        model = LegalClient
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = None
        # check if the email is already registered
        return LegalClient.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = None

        if validated_data['status'] == 1:
            try:
                data = {
                    "role": "7c668ceb-665e-42f0-b67a-f3c5781abd0f",
                    "type_client": instance.typeClient.id,
                    "type_identity": '6b1a9326-00c6-4b72-a8b4-4453b889fbb7',
                    "document_number": instance.nit + instance.verificationDigit,
                    "first_name": "",
                    "last_name": "",
                    "birth_date":instance.dateOfConstitution,
                    "address": instance.principalAddress,
                    "phone_number": instance.companyPhone,
                    "description": instance.companyName,
                    "social_reason": instance.companyName,
                    "city": instance.city.id,
                    "broker": None,
                    "email": instance.companyEmail,
                    "citizenship": '9729f179-298e-4616-8aa4-3ce44dd18449',
                    "department": instance.department.id,
                    "entered_by": self.context['request'].user.id,
                    "user": None,
                    "ciiu": instance.ciiu.id,
                }
                # create a user for the client
                user = UserSerializer(data=data, context={'request':self.context['request']})
                if user.is_valid():
                    #Save the user
                    user.save()
                    # get the user
                    data['user'] = UserSerializer.Meta.model.objects.get(email=instance.companyEmail).id
                    #create the client
                    client = ClientSerializer(data=data, context={'request':self.context['request']})
                    if client.is_valid():
                        client.save()
                        LR = LegalRepresentativeSerializer(data={
                                    "client": client.data['id'],
                                    "type_identity": instance.legalRepresentativeTypeDocument.id,
                                    "document_number": instance.legalRepresentativeDocumentNumber,
                                    "first_name": instance.legalRepresentativeName,
                                    "last_name": instance.legalRepresentativeLastName,
                                    "city": instance.legalRepresentativeCity.id,
                                    "citizenship": instance.legalRepresentativeCountry.id,
                                    "birth_date": instance.legalRepresentativeBirthDate,
                                    "address": "no aplica",
                                    "phone_number": instance.legalRepresentativePhone,
                                    "email": instance.legalRepresentativeEmail,
                                    "position": instance.legalRepresentativePosition,
                                    
                                }, context={'request': self.context['request']})
                        if LR.is_valid():
                            LR.save()
                        
                        # create the account
                        account = AccountSerializer(data={
                                "client": client.data['id'],
                                "primary": True,
                                "account_number": random_with_N_digits(10),
                            }, context={'request':self.context['request']})
                        if account.is_valid():
                            account.save()

                        # get the legal client contacts
                        dataContacts = LegalClientContacts.objects.filter(legalClient=instance.id)

                        for contact in dataContacts:
                            data = {
                                "client": client.data['id'],
                                'first_name': contact.name,
                                'email': contact.email,
                                'position': contact.position,
                                'phone_number': contact.phone,
                            }
                            contact = ContactSerializer(data=data, context={'request':self.context['request']})
                            if contact.is_valid():
                                contact.save()
            except Exception as e:
                    UserSerializer.Meta.model.objects.get(email=instance.email).delete()
                    raise serializers.ValidationError("Error al crear el cliente")
        elif validated_data['status'] == 2:
            try:
                if instance.status == 0:
                    # get the client
                    client = Client.objects.get(email=instance.companyEmail)
                    # delete the client
                    client.delete()
                    # delete the user 
                    user = User.objects.get(email=instance.companyEmail)
                    user.delete()
            except Exception as e:
                raise HttpException(400, str(e))

        return super().update(instance, validated_data)

class LegalClientReadOnlySerializer(serializers.ModelSerializer):
    ciiu = CIIUReadOnlySerializer()
    financialRelations = serializers.SerializerMethodField(method_name='get_financial_relations')
    legalClientContacts = serializers.SerializerMethodField(method_name='get_legal_client_contacts')
    managementBoard = serializers.SerializerMethodField(method_name='get_management_board')
    partnersAndShareHolders = serializers.SerializerMethodField(method_name='get_partners_and_shareholders')
    principalClients = serializers.SerializerMethodField(method_name='get_principal_clients')
    principalCompetitors = serializers.SerializerMethodField(method_name='get_principal_competitors')
    principalProducts = serializers.SerializerMethodField(method_name='get_principal_products')
    principalProviders = serializers.SerializerMethodField(method_name='get_principal_providers')
    legalRepresentativeCountry = CountrySerializer()
    foreignAccountCountry = CountrySerializer()
    department = DepartmentSerializer()
    city = CitySerializer()
    country = CountrySerializer()
    legalRepresentativeTypeDocument = TypeIdentitySerializer()
    isSignatureSent = serializers.SerializerMethodField(method_name='get_is_signature_sent')
    isSignatureSigned = serializers.SerializerMethodField(method_name='get_is_signature_signed')
    

    class Meta:
        model = LegalClient
        fields = '__all__'

    def get_financial_relations(self, obj):
        return FinancialRelations.objects.filter(legalClient=obj).values()

    def get_legal_client_contacts(self, obj):
        return LegalClientContacts.objects.filter(legalClient=obj).values()

    def get_management_board(self, obj):
        return ManagementBoard.objects.filter(legalClient=obj).values()

    def get_partners_and_shareholders(self, obj):
        return PartnersAndShareholders.objects.filter(legalClient=obj).values()

    def get_principal_clients(self, obj):
        return PrincipalClients.objects.filter(legalClient=obj).values()

    def get_principal_competitors(self, obj):
        return PrincipalCompetitors.objects.filter(legalClient=obj).values()
    
    def get_principal_products(self, obj):
        return PrincipalProducts.objects.filter(legalClient=obj).values()
    
    def get_principal_providers(self, obj):
        return PrincipalProviders.objects.filter(legalClient=obj).values()
    
    def get_is_signature_sent(self, obj):
        try:
            # check if the signature is sent
            signature = LegalClientDocuments.objects.get(legalClient=obj.id)
            return True
        except:
            return False
    
    def get_is_signature_signed(self, obj):
        try:
            # check if the signature is sent
            signature = LegalClientDocuments.objects.get(legalClient=obj)
            body = {
                    "request": "GET_SIGNATURE_STATUS",
                    "signature_id": signature.idSignature,
                    "user": "smartevolution@co",
                    "password": "brtSji0_nQ",
                }
            res = requests.post('https://api.lleida.net/cs/v1/get_signature_status', json=body)
            # check is sign status is signed
            if res.json()['signature_status'] == 'signed':
                return res.json()['signature_status_date']
            else:
                return None
            
        except:
            return None
    

class NaturalClientSerializer(serializers.ModelSerializer):
    documentFile          = PDFBase64File()
    rentDeclarationFile   = PDFBase64File()
    bankCertificationFile = PDFBase64File()
    class Meta:
        model = NaturalClient
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = None
        return NaturalClient.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = None
        try:
            if validated_data['status'] == 1:
                # create the client
                data = {
                        "role": "7c668ceb-665e-42f0-b67a-f3c5781abd0f",
                        "type_client": '26c885fc-2a53-4199-a6c1-7e4e92032696',
                        "type_identity": instance.typeDocument.id,
                        "document_number": instance.documentNumber,
                        "first_name": instance.firstName if instance.firstName else '',
                        "last_name": instance.lastName if instance.lastName else '',
                        "birth_date":instance.birthDate if instance.birthDate else '',
                        "address": instance.address,
                        "phone_number": instance.phone,
                        "description": instance.companyName,
                        "social_reason": None,
                        "city": instance.city.id,
                        "broker": None,
                        "email": instance.email,
                        "citizenship": '9729f179-298e-4616-8aa4-3ce44dd18449',
                        "department": instance.department.id,
                        "entered_by": self.context['request'].user.id,
                        "user": None,
                        "ciiu": instance.ciiu.id if instance.ciiu else None,
                    }

                # create a user for the client
                user = UserSerializer(data=data, context={'request':self.context['request']})
                if user.is_valid():
                    #Save the user
                    user.save()
                    # get the user
                    data['user'] = UserSerializer.Meta.model.objects.get(email=instance.email).id
                    #create the client
                    client = ClientSerializer(data=data, context={'request':self.context['request']})
                    if client.is_valid():
                        client.save()
                        LR = LegalRepresentativeSerializer(data={
                                        "client": client.data['id'],
                                        "type_identity": instance.typeDocument.id,
                                        "document_number": instance.documentNumber,
                                        "first_name": instance.firstName if instance.firstName else '',
                                        "last_name": instance.lastName if instance.lastName else '',
                                        "citizenship":'9729f179-298e-4616-8aa4-3ce44dd18449',
                                        "city": instance.city.id,
                                        "address": "no aplica",
                                        "phone_number": instance.phone,
                                        "email": instance.email,
                                        "position": 'representante legal',
                                    }, context={'request': self.context['request']})

                        if LR.is_valid():
                                LR.save()
                        
                    # create the account
                    account = AccountSerializer(data={
                            "client": client.data['id'],
                            "primary": True,
                            "account_number": random_with_N_digits(10),
                        }, context={'request':self.context['request']})
                    if account.is_valid():
                        account.save()
                else:
                    raise HttpException(400, str(user.errors))
            elif validated_data['status'] == 2:
                try:
                    if instance.status == 0:
                        # get the client
                        client = Client.objects.get(email=instance.email)
                        # delete the client
                        client.delete()
                        # delete the user 
                        user = User.objects.get(email=instance.email)
                        user.delete()
                    #sendWhatsApp('Su solicitud de registro ha sido rechazada',instance.companyPhone)
                except Exception as e:
                    pass
            return super().update(instance, validated_data)
        except Exception as e:
            raise str(e)


class NaturalClientReadOnlySerializer(serializers.ModelSerializer):
    ciiu = CIIUReadOnlySerializer()
    secondaryCiiu = CIIUReadOnlySerializer()
    activityType  = CIIUReadOnlySerializer()
    typeDocument = TypeIdentitySerializer()
    country = CountrySerializer()
    city = CitySerializer()
    department = DepartmentSerializer()
    companyDepartment = DepartmentSerializer()
    companyCity = CitySerializer()
    referenceCity= CitySerializer()
    referenceDepartment = DepartmentSerializer()
    referenceBankDepartment = DepartmentSerializer()
    referenceBankCity = CitySerializer()
    isSignatureSent = serializers.SerializerMethodField(method_name='get_isSignatureSent')
    isSignatureSigned = serializers.SerializerMethodField(method_name='get_isSignatureSigned')

    class Meta:
        model = NaturalClient
        fields = '__all__'

    def get_isSignatureSent(self, obj):
        try:
            signature = NaturalClientDocuments.objects.get(naturalClient=obj.id)
            return True
        except:
            return False

    def get_isSignatureSigned(self, obj):
        try:
            # check if the signature is sent
            signature = NaturalClientDocuments.objects.get(naturalClient=obj)
            body = {
                    "request": "GET_SIGNATURE_STATUS",
                    "signature_id": signature.idSignature,
                    "user": "smartevolution@co",
                    "password": "brtSji0_nQ",
                }
            res = requests.post('https://api.lleida.net/cs/v1/get_signature_status', json=body)
            # check is sign status is signed
            if res.json()['signature_status'] == 'signed':
                return res.json()['signature_status_date']
            else:
                return None
            
        except:
            return None

class LegalClientDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalClientDocuments
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id']              = gen_uuid()
        validated_data['created_at']      = timezone.now()
        validated_data['user_created_at'] = None
        return  super().create(validated_data)

class NaturalClientDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturalClientDocuments
        fields = '__all__'

    def create(self, validated_data):
        validated_data['id']              = gen_uuid()
        validated_data['created_at']      = timezone.now()
        validated_data['user_created_at'] = None
        return  super().create(validated_data)