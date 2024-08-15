from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .api.models.index import (
    Broker,
    Client,
    Contact,
    LegalRepresentative,
    Account,
    AccountBalanceHistory,
    Request,
    RiskProfile,
    Assets,
    Passives,
    Patrimony,
    StateOfResult,
    FinancialProfile,
    FinancialCentral,
    Overview,
    LegalClient,
    FinancialRelations,
    LegalClientContacts,
    ManagementBoard,
    PartnersAndShareholders,
    PrincipalClients,
    PrincipalCompetitors,
    PrincipalProducts,
    PrincipalProviders,
    NaturalClient,
    LegalClientDocuments,
    NaturalClientDocuments
)

LIST_PER_PAGE = 20

class BrokerResource(resources.ModelResource):
    class Meta:
        model = Broker
        fields = '__all__'
        import_id_fields = ('id',)

class ClientResource(resources.ModelResource):
    class Meta:
        model = Client
        fields = '__all__'
        import_id_fields = ('id',)

class ContactResource(resources.ModelResource):
    class Meta:
        model = Contact
        fields = '__all__'
        import_id_fields = ('id',)

class LegalRepresentativeResource(resources.ModelResource):
    class Meta:
        model = LegalRepresentative
        fields = '__all__'
        import_id_fields = ('id',)

class AccountResource(resources.ModelResource):
    class Meta:
        model = Account
        fields = '__all__'
        import_id_fields = ('id',)

class AccountBalanceHistoryResource(resources.ModelResource):
    class Meta:
        model = AccountBalanceHistory
        fields = '__all__'
        import_id_fields = ('id',)

class RequestResource(resources.ModelResource):
    class Meta:
        model = Request
        fields = '__all__'
        import_id_fields = ('id',)

class RiskProfileResource(resources.ModelResource):
    class Meta:
        model = RiskProfile
        fields = '__all__'
        import_id_fields = ('id',)

class AssetsResource(resources.ModelResource):
    class Meta:
        model = Assets
        fields = '__all__'
        import_id_fields = ('id',)

class PassivesResource(resources.ModelResource):
    class Meta:
        model = Passives
        fields = '__all__'
        import_id_fields = ('id',)

class PatrimonyResource(resources.ModelResource):
    class Meta:
        model = Patrimony
        fields = '__all__'
        import_id_fields = ('id',)

class StateOfResultResource(resources.ModelResource):
    class Meta:
        model = StateOfResult
        fields = '__all__'
        import_id_fields = ('id',)

class FinancialProfileResource(resources.ModelResource):
    class Meta:
        model = FinancialProfile
        fields = '__all__'
        import_id_fields = ('id',)

class FinancialCentralResource(resources.ModelResource):
    class Meta:
        model = FinancialCentral
        fields = '__all__'
        import_id_fields = ('id',)

class OverviewResource(resources.ModelResource):
    class Meta:
        model = Overview
        fields = '__all__'
        import_id_fields = ('id',)

class LegalClientResource(resources.ModelResource):
    class Meta:
        model = LegalClient
        fields = '__all__'
        import_id_fields = ('id',)

class FinancialRelationsResource(resources.ModelResource):
    class Meta:
        model = FinancialRelations
        fields = '__all__'
        import_id_fields = ('id',)

class LegalClientContactsResource(resources.ModelResource):
    class Meta:
        model = LegalClientContacts
        fields = '__all__'
        import_id_fields = ('id',)

class ManagementBoardResource(resources.ModelResource):
    class Meta:
        model = ManagementBoard
        fields = '__all__'
        import_id_fields = ('id',)

class PartnersAndShareholdersResource(resources.ModelResource):
    class Meta:
        model = PartnersAndShareholders
        fields = '__all__'
        import_id_fields = ('id',)

class PrincipalClientsResource(resources.ModelResource):
    class Meta:
        model = PrincipalClients
        fields = '__all__'
        import_id_fields = ('id',)

class PrincipalCompetitorsResource(resources.ModelResource):
    class Meta:
        model = PrincipalCompetitors
        fields = '__all__'
        import_id_fields = ('id',)

class PrincipalProductsResource(resources.ModelResource):
    class Meta:
        model = PrincipalProducts
        fields = '__all__'
        import_id_fields = ('id',)

class PrincipalProvidersResource(resources.ModelResource):
    class Meta:
        model = PrincipalProviders
        fields = '__all__'
        import_id_fields = ('id',)

class NaturalClientResource(resources.ModelResource):
    class Meta:
        model = NaturalClient
        fields = '__all__'
        import_id_fields = ('id',)

class LegalClientDocumentsResource(resources.ModelResource):
    class Meta:
        model = LegalClientDocuments
        fields = '__all__'
        import_id_fields = ('id',)

class NaturalClientDocumentsResource(resources.ModelResource):
    class Meta:
        model = NaturalClientDocuments
        fields = '__all__'
        import_id_fields = ('id',)

@admin.register(Broker)
class BrokerAdmin(ImportExportModelAdmin):
    resource_class = BrokerResource
    list_display = ('id', 'type_identity', 'document_number', 'first_name', 'last_name', 'email', 'phone_number',)
    search_fields = ('type_identity', 'document_number', 'first_name', 'last_name', 'email', 'phone_number')
    list_filter = ('type_identity', 'document_number', 'first_name', 'last_name', 'email', 'phone_number')
    list_per_page = LIST_PER_PAGE

@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource
    list_display = ('id', 'type_client', 'first_name', 'last_name', 'social_reason', 'email', 'phone_number',)
    search_fields = ('type_client', 'first_name', 'last_name', 'social_reason', 'email', 'phone_number',)
    list_filter = ('type_client', 'first_name', 'last_name', 'social_reason', 'email', 'phone_number',)
    list_per_page = LIST_PER_PAGE

@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin):
    resource_class = ContactResource
    list_display = ('id', 'client', 'first_name', 'last_name', 'phone_number', 'email',)
    search_fields = ('client', 'first_name', 'last_name', 'phone_number', 'email',)
    list_filter = ('client', 'first_name', 'last_name', 'phone_number', 'email',)
    list_per_page = LIST_PER_PAGE

@admin.register(LegalRepresentative)
class LegalRepresentativeAdmin(ImportExportModelAdmin):
    resource_class = LegalRepresentativeResource
    list_display = ('id', 'client', 'document_number', 'first_name', 'last_name', 'phone_number', 'email',)
    search_fields = ('client', 'document_number', 'first_name', 'last_name', 'phone_number', 'email',)
    list_filter = ('client', 'document_number', 'first_name', 'last_name', 'phone_number', 'email',)
    list_per_page = LIST_PER_PAGE

@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    resource_class = AccountResource
    list_display = ('id', 'client', 'account_number', 'balance',)
    search_fields = ('client', 'account_number', 'balance',)
    list_filter = ('client', 'account_number', 'balance',)
    list_per_page = LIST_PER_PAGE

@admin.register(AccountBalanceHistory)
class AccountBalanceHistoryAdmin(ImportExportModelAdmin):
    resource_class = AccountBalanceHistoryResource
    list_display = ('id', 'account', 'old_balance', 'new_balance', 'amount_changed', 'operation_type',)
    search_fields = ('account', 'old_balance', 'new_balance', 'amount_changed', 'operation_type',)
    list_filter = ('account', 'old_balance', 'new_balance', 'amount_changed', 'operation_type',)
    list_per_page = LIST_PER_PAGE

@admin.register(Request)
class RequestAdmin(ImportExportModelAdmin):
    resource_class = RequestResource
    list_display = ('id', 'client', 'status',)
    search_fields = ('status', 'client',)
    list_filter = ('status', 'client',)
    list_per_page = LIST_PER_PAGE

@admin.register(RiskProfile)
class RiskProfileAdmin(ImportExportModelAdmin):
    resource_class = RiskProfileResource
    list_display = ('id', 'client', 'emitter_balance', 'payer_balance', 'account_type', 'account_number',)
    search_fields = ('client', 'emitter_balance', 'payer_balance',)
    list_filter = ('client', 'emitter_balance', 'payer_balance',)
    list_per_page = LIST_PER_PAGE

@admin.register(Assets)
class AssetsAdmin(ImportExportModelAdmin):
    resource_class = AssetsResource
    list_display = ('id', 'cash_and_investments', 'clients_wallet', 'total_inventory', 'total_assets',)
    search_fields = ('cash_and_investments', 'clients_wallet', 'total_inventory', 'total_assets',)
    list_filter = ('cash_and_investments', 'clients_wallet', 'total_inventory', 'total_assets',)
    list_per_page = LIST_PER_PAGE

@admin.register(Passives)
class PassivesAdmin(ImportExportModelAdmin):
    resource_class = PassivesResource
    list_display = ('id', 'financial_obligation_cp', 'providers', 'unpaid_expenses',)
    search_fields = ('financial_obligation_cp', 'providers', 'unpaid_expenses',)
    list_filter = ('financial_obligation_cp', 'providers', 'unpaid_expenses',)
    list_per_page = LIST_PER_PAGE

@admin.register(Patrimony)
class PatrimonyAdmin(ImportExportModelAdmin):
    resource_class = PatrimonyResource
    list_display = ('id', 'payed_capital', 'sup_capital_prima', 'legal_reserve', 'periods_results',)
    search_fields = ('payed_capital', 'sup_capital_prima', 'legal_reserve',)
    list_filter = ('payed_capital', 'sup_capital_prima', 'legal_reserve',)
    list_per_page = LIST_PER_PAGE

@admin.register(StateOfResult)
class StateOfResultAdmin(ImportExportModelAdmin):
    resource_class = StateOfResultResource
    list_display = ('id', 'gross_sale', 'dtos_returns', 'net_sales', 'cost_of_sales',)
    search_fields = ('gross_sale', 'dtos_returns', 'net_sales', 'cost_of_sales',)
    list_filter = ('gross_sale', 'dtos_returns', 'net_sales', 'cost_of_sales',)
    list_per_page = LIST_PER_PAGE

@admin.register(FinancialProfile)
class FinancialProfileAdmin(ImportExportModelAdmin):
    resource_class = FinancialProfileResource
    list_display = ('id', 'period', 'periodRange', 'periodDays', 'periodStartDate', 'periodEndDate', 'balance',)
    search_fields = ('period', 'periodRange', 'periodDays',)
    list_filter = ('period', 'periodRange', 'periodDays',)
    list_per_page = LIST_PER_PAGE

@admin.register(FinancialCentral)
class FinancialCentralAdmin(ImportExportModelAdmin):
    resource_class = FinancialCentralResource
    list_display = ('id', 'client', 'centralBalances', 'rating',)
    search_fields = ('client', 'centralBalances', 'rating',)
    list_filter = ('client', 'centralBalances', 'rating',)
    list_per_page = LIST_PER_PAGE

@admin.register(Overview)
class OverviewAdmin(ImportExportModelAdmin):
    resource_class = OverviewResource
    list_display = ('id', 'client', 'qualitativeOverview', 'financialAnalisis',)
    search_fields = ('client', 'qualitativeOverview', 'financialAnalisis',)
    list_filter = ('client', 'qualitativeOverview', 'financialAnalisis',)
    list_per_page = LIST_PER_PAGE

@admin.register(LegalClient)
class LegalClientAdmin(ImportExportModelAdmin):
    resource_class = LegalClientResource
    list_display = ('id', 'email', 'typeClient', 'companyName', 'country',)
    search_fields = ('email', 'typeClient', 'companyName', 'country',)
    list_filter = ('email', 'typeClient', 'companyName', 'country',)
    list_per_page = LIST_PER_PAGE

@admin.register(FinancialRelations)
class FinancialRelationsAdmin(ImportExportModelAdmin):
    resource_class = FinancialRelationsResource
    list_display = ('id', 'legalClient', 'name', 'amount', 'tax',)
    search_fields = ('legalClient', 'name', 'amount', 'tax',)
    list_filter = ('legalClient', 'name', 'amount', 'tax',)
    list_per_page = LIST_PER_PAGE

@admin.register(LegalClientContacts)
class LegalClientContactsAdmin(ImportExportModelAdmin):
    resource_class = LegalClientContactsResource
    list_display = ('id', 'legalClient', 'name', 'area', 'phone', 'email',)
    search_fields = ('legalClient', 'name', 'area', 'phone', 'email',)
    list_filter = ('legalClient', 'name', 'area', 'phone', 'email',)
    list_per_page = LIST_PER_PAGE

@admin.register(ManagementBoard)
class ManagementBoardAdmin(ImportExportModelAdmin):
    resource_class = ManagementBoardResource
    list_display = ('id', 'legalClient', 'name', 'type',)
    search_fields = ('legalClient', 'name', 'type',)
    list_filter = ('legalClient', 'name', 'type',)
    list_per_page = LIST_PER_PAGE

@admin.register(PartnersAndShareholders)
class PartnersAndShareholdersAdmin(ImportExportModelAdmin):
    resource_class = PartnersAndShareholdersResource
    list_display = ('id', 'legalClient', 'name', 'documentNumber', 'percentage',)
    search_fields = ('legalClient', 'name', 'documentNumber', 'percentage',)
    list_filter = ('legalClient', 'name', 'documentNumber', 'percentage',)
    list_per_page = LIST_PER_PAGE

@admin.register(PrincipalClients)
class PrincipalClientsAdmin(ImportExportModelAdmin):
    resource_class = PrincipalClientsResource
    list_display = ('id', 'legalClient', 'name', 'salePercentage', 'contactName',)
    search_fields = ('legalClient', 'name', 'salePercentage', 'contactName',)
    list_filter = ('legalClient', 'name', 'salePercentage', 'contactName',)
    list_per_page = LIST_PER_PAGE

@admin.register(PrincipalCompetitors)
class PrincipalCompetitorsAdmin(ImportExportModelAdmin):
    resource_class = PrincipalCompetitorsResource
    list_display = ('id', 'legalClient', 'name', 'percentage',)
    search_fields = ('legalClient', 'name', 'percentage',)
    list_filter = ('legalClient', 'name', 'percentage',)
    list_per_page = LIST_PER_PAGE

@admin.register(PrincipalProducts)
class PrincipalProductsAdmin(ImportExportModelAdmin):
    resource_class = PrincipalProductsResource
    list_display = ('id', 'legalClient', 'name', 'percentage',)
    search_fields = ('legalClient', 'name', 'percentage',)
    list_filter = ('legalClient', 'name', 'percentage',)
    list_per_page = LIST_PER_PAGE

@admin.register(PrincipalProviders)
class PrincipalProvidersAdmin(ImportExportModelAdmin):
    resource_class = PrincipalProvidersResource
    list_display = ('id', 'legalClient', 'name', 'salePercentage', 'contactName', 'phone',)
    search_fields = ('legalClient', 'name', 'salePercentage', 'contactName', 'phone',)
    list_filter = ('legalClient', 'name', 'salePercentage', 'contactName', 'phone',)
    list_per_page = LIST_PER_PAGE

@admin.register(NaturalClient)
class NaturalClientAdmin(ImportExportModelAdmin):
    resource_class = NaturalClientResource
    list_display = ('id', 'firstName', 'lastName', 'email', 'phone', 'companyName',)
    search_fields = ('firstName', 'lastName', 'email', 'phone',)
    list_filter = ('firstName', 'lastName', 'email', 'phone',)
    list_per_page = LIST_PER_PAGE

@admin.register(LegalClientDocuments)
class LegalClientDocumentsAdmin(ImportExportModelAdmin):
    resource_class = LegalClientDocumentsResource
    list_display = ('id', 'legalClient', 'date', 'status',)
    search_fields = ('legalClient', 'date', 'status',)
    list_filter = ('legalClient', 'date', 'status',)
    list_per_page = LIST_PER_PAGE

@admin.register(NaturalClientDocuments)
class NaturalClientDocumentsAdmin(ImportExportModelAdmin):
    resource_class = NaturalClientDocumentsResource
    list_display = ('id', 'naturalClient', 'date', 'status',)
    search_fields = ('naturalClient', 'date', 'status',)
    list_filter = ('naturalClient', 'date', 'status',)
    list_per_page = LIST_PER_PAGE