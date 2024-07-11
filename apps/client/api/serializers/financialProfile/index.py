# Rest Framework
from rest_framework import serializers
# Models
from apps.client.models import FinancialProfile
# Serializers
from apps.client.api.serializers.financialProfile.financialSituation.assets.index import AssetsSerializer
from apps.client.api.serializers.financialProfile.financialSituation.passives.index import PassivesSerializer
from apps.client.api.serializers.financialProfile.financialSituation.patrimony.index import PatrimonySerializer
from apps.client.api.serializers.financialProfile.financialSituation.stateOfResult.index import StateOfResultSerializer
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid, PDFBase64File
from django.utils.translation import gettext as _


class FinancialProfileSerializer(serializers.ModelSerializer):
    balance                     = PDFBase64File()
    stateOfCashflow             = PDFBase64File()
    financialStatementAudit     = PDFBase64File()
    managementReport            = PDFBase64File()
    certificateOfStockOwnership = PDFBase64File()
    rentDeclaration             = PDFBase64File()
    class Meta:
        model = FinancialProfile
        fields = "__all__"

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        # Verify if the period already exists
        if FinancialProfile.objects.filter(client=validated_data['client'], period=validated_data['period']).exists():
            raise serializers.ValidationError('Este periodo ya se encuentra registrado')
        FinancialProfile.objects.create(**validated_data)        
        return validated_data

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        if '_assets' in self.context['request'].data:   
            # verify if the assets already exists
            if not instance.assets:
                assets = AssetsSerializer(data=self.context['request'].data['_assets'], context={'request':self.context['request']})
                if assets.is_valid():
                    assets.save()
                else:
                    raise assets.errors
            else:
                # get the assets instance and update it
                assets = instance.assets
                assets_serializer = AssetsSerializer(assets, data=self.context['request'].data['_assets'], context={'request':self.context['request']}, partial=True)
                if assets_serializer.is_valid():
                    assets_serializer.save()
        if '_passives' in self.context['request'].data:
            # verify if the passives already exists
            if not instance.passives:
                passives = PassivesSerializer(data=self.context['request'].data['_passives'], context={'request':self.context['request']})
                if passives.is_valid():
                    passives.save()
            else:
                # get the passives instance and update it
                passives = instance.passives
                passives_serializer = PassivesSerializer(passives, data=self.context['request'].data['_passives'], context={'request':self.context['request']}, partial=True)
                if passives_serializer.is_valid():
                    passives_serializer.save()
        if '_patrimony' in self.context['request'].data:
            # verify if the patrimony already exists
            if not instance.patrimony:
                patrimony = PatrimonySerializer(data=self.context['request'].data['_patrimony'], context={'request':self.context['request']})
                if patrimony.is_valid():
                    patrimony.save()
            else:
                # get the patrimony instance and update it
                patrimony = instance.patrimony
                patrimony_serializer = PatrimonySerializer(patrimony, data=self.context['request'].data['_patrimony'], context={'request':self.context['request']}, partial=True)
                if patrimony_serializer.is_valid():
                    patrimony_serializer.save()
        if '_stateOfResult' in self.context['request'].data:
            # verify if the state_of_result already exists
            if not instance.stateOfResult:
                state_of_result = StateOfResultSerializer(data=self.context['request'].data['_stateOfResult'], context={'request':self.context['request']})
                if state_of_result.is_valid():
                    state_of_result.save()
            else:
                # get the state_of_result instance and update it
                state_of_result = instance.stateOfResult
                state_of_result_serializer = StateOfResultSerializer(state_of_result, data=self.context['request'].data['_stateOfResult'], context={'request':self.context['request']}, partial=True)
                if state_of_result_serializer.is_valid():
                    state_of_result_serializer.save()
        return super().update(instance, validated_data)


class FinancialProfileUpdateSerializer(serializers.ModelSerializer):
    balance                     = PDFBase64File()
    stateOfCashflow             = PDFBase64File()
    financialStatementAudit     = PDFBase64File()
    managementReport            = PDFBase64File()
    certificateOfStockOwnership = PDFBase64File()
    rentDeclaration             = PDFBase64File()
    dateRanges                  = serializers.SerializerMethodField(method_name='get_date_ranges')
    class Meta:
        model = FinancialProfile
        fields = "__all__"

    def create(self, validated_data):
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        # Verify if the period already exists
        if FinancialProfile.objects.filter(client=validated_data['client'], period=validated_data['period']).exists():
            raise serializers.ValidationError('Este periodo ya se encuentra registrado')
        FinancialProfile.objects.create(**validated_data)        
        return validated_data

    def update(self, instance, validated_data):
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user
        if '_assets' in self.context['request'].data:   
            # verify if the assets already exists
            if not instance.assets:
                assets = AssetsSerializer(data=self.context['request'].data['_assets'], context={'request':self.context['request']})
                if assets.is_valid():
                    assets.save()
                else:
                    raise assets.errors
            else:
                # get the assets instance and update it
                assets = instance.assets
                assets_serializer = AssetsSerializer(assets, data=self.context['request'].data['_assets'], context={'request':self.context['request']}, partial=True)
                if assets_serializer.is_valid():
                    assets_serializer.save()
        if '_passives' in self.context['request'].data:
            # verify if the passives already exists
            if not instance.passives:
                passives = PassivesSerializer(data=self.context['request'].data['_passives'], context={'request':self.context['request']})
                if passives.is_valid():
                    passives.save()
            else:
                # get the passives instance and update it
                passives = instance.passives
                passives_serializer = PassivesSerializer(passives, data=self.context['request'].data['_passives'], context={'request':self.context['request']}, partial=True)
                if passives_serializer.is_valid():
                    passives_serializer.save()
        if '_patrimony' in self.context['request'].data:
            # verify if the patrimony already exists
            if not instance.patrimony:
                patrimony = PatrimonySerializer(data=self.context['request'].data['_patrimony'], context={'request':self.context['request']})
                if patrimony.is_valid():
                    patrimony.save()
            else:
                # get the patrimony instance and update it
                patrimony = instance.patrimony
                patrimony_serializer = PatrimonySerializer(patrimony, data=self.context['request'].data['_patrimony'], context={'request':self.context['request']}, partial=True)
                if patrimony_serializer.is_valid():
                    patrimony_serializer.save()
        if '_stateOfResult' in self.context['request'].data:
            # verify if the state_of_result already exists
            if not instance.stateOfResult:
                state_of_result = StateOfResultSerializer(data=self.context['request'].data['_stateOfResult'], context={'request':self.context['request']})
                if state_of_result.is_valid():
                    state_of_result.save()
            else:
                # get the state_of_result instance and update it
                state_of_result = instance.stateOfResult
                state_of_result_serializer = StateOfResultSerializer(state_of_result, data=self.context['request'].data['_stateOfResult'], context={'request':self.context['request']}, partial=True)
                if state_of_result_serializer.is_valid():
                    state_of_result_serializer.save()
        return super().update(instance, validated_data)

    def get_date_ranges(self, obj):
        if obj.typePeriod.id == '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
            return f'ENE - DIC {obj.period}'
        elif obj.typePeriod.id == 'e635f0f1-b29c-45e5-b351-04725a489be3':
            if obj.periodRange.id == '2f1d5c8d-36ef-4b1a-a76a-91b9f60363f7':
                return f'ENE - JUN {obj.period}'
            else:
                return f'AGO - DIC {obj.period}'
        elif obj.typePeriod.id == 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
            if obj.periodRange == 'e2b93f89-dbd9-48fc-828f-f7170771c819':
                return f'ENE - MAR {obj.period}'
            elif obj.periodRange == 'ec4506b5-3440-4208-85e4-3b64b80261e2':
                return f'ABR - JUN {obj.period}'
            elif obj.periodRange == '6a8a9448-854a-4353-bbb6-70c39a7678b8':
                return f'JUL - SEP {obj.period}'
            else:
                return f'OCT - DIC {obj.period}'
        else:
            # get the month name of the start date in spanish
            startMonth = (_(obj.periodStartDate.strftime('%B'))[0:3]).upper()
            # get the month name of the end date
            endMonth = (_(obj.periodEndDate.strftime('%B'))[0:3]).upper()
            return f'{startMonth} - {endMonth} {obj.period}'


class FinancialProfileReadOnlySerializer(serializers.ModelSerializer):
    assets        = AssetsSerializer()
    passives      = PassivesSerializer()
    patrimony     = PatrimonySerializer()
    stateOfResult = StateOfResultSerializer()
    dateRanges    = serializers.SerializerMethodField(method_name='get_date_ranges')

    class Meta:
        model = FinancialProfile
        fields = "__all__"

    def get_date_ranges(self, obj):
        if obj.typePeriod.id == '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
            return f'ENE - DIC {obj.period}'
        elif obj.typePeriod.id == 'e635f0f1-b29c-45e5-b351-04725a489be3':
            if obj.periodRange.id == '2f1d5c8d-36ef-4b1a-a76a-91b9f60363f7':
                return f'ENE - JUN {obj.period}'
            else:
                return f'AGO - DIC {obj.period}'
        elif obj.typePeriod.id == 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
            if obj.periodRange == 'e2b93f89-dbd9-48fc-828f-f7170771c819':
                return f'ENE - MAR {obj.period}'
            elif obj.periodRange == 'ec4506b5-3440-4208-85e4-3b64b80261e2':
                return f'ABR - JUN {obj.period}'
            elif obj.periodRange == '6a8a9448-854a-4353-bbb6-70c39a7678b8':
                return f'JUL - SEP {obj.period}'
            else:
                return f'OCT - DIC {obj.period}'
        else:
            # get the month name of the start date in spanish
            startMonth = (_(obj.periodStartDate.strftime('%B'))[0:3]).upper()
            # get the month name of the end date
            endMonth = (_(obj.periodEndDate.strftime('%B'))[0:3]).upper()
            return f'{startMonth} - {endMonth} {obj.period}'


class FinancialProfilePeriodSerializer(serializers.ModelSerializer):
    assets        = AssetsSerializer()
    passives      = PassivesSerializer()
    patrimony     = PatrimonySerializer()
    stateOfResult = StateOfResultSerializer()

    class Meta:
        model = FinancialProfile
        fields = "__all__"

