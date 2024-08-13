from django.contrib import admin
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
@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_identity', 'document_number', 'first_name', 'last_name', 'email', 'phone_number',) 
    search_fields = ('type_identity', 'document_number', 'first_name', 'last_name', 'email', 'phone_number')
    list_filter = ('type_identity', 'document_number', 'first_name', 'last_name', 'email', 'phone_number')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_client', 'first_name', 'last_name', 'social_reason', 'email', 'phone_number', ) 
    search_fields = ('type_client', 'first_name', 'last_name', 'social_reason', 'email', 'phone_number',)
    list_filter = ('type_client', 'first_name', 'last_name', 'social_reason', 'email', 'phone_number',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'first_name', 'last_name', 'phone_number', 'email', ) 
    search_fields = ('client', 'first_name', 'last_name', 'phone_number', 'email',)
    list_filter = ('client', 'first_name', 'last_name', 'phone_number', 'email',)

@admin.register(LegalRepresentative)
class LegalRepresentativeAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'document_number', 'first_name', 'last_name', 'phone_number', 'email',) 
    search_fields = ('client', 'document_number', 'first_name', 'last_name', 'phone_number', 'email',)
    list_filter = ('client', 'document_number', 'first_name', 'last_name', 'phone_number', 'email',)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'account_number', 'balance',) 
    search_fields = ('client', 'account_number', 'balance',)
    list_filter = ('client', 'account_number', 'balance',)

@admin.register(AccountBalanceHistory)
class AccountBalanceHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'old_balance', 'new_balance', 'amount_changed', 'operation_type') 
    search_fields = ('account', 'old_balance', 'new_balance', 'amount_changed', 'operation_type')
    list_filter = ('account', 'old_balance', 'new_balance', 'amount_changed', 'operation_type')

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'status') 
    search_fields = ('status', 'client',)
    list_filter = ('status', 'client',)

@admin.register(RiskProfile)
class RiskProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'emitter_balance', 'payer_balance', 'account_type', 'account_number',) 
    search_fields = ('client', 'emitter_balance', 'payer_balance',)
    list_filter = ('client', 'emitter_balance', 'payer_balance',)

@admin.register(Assets)
class AssetsAdmin(admin.ModelAdmin):
    list_display = ('id', 'cash_and_investments', 'clients_wallet', 'total_inventory', 'total_assets') 
    search_fields = ('cash_and_investments', 'clients_wallet', 'total_inventory', 'total_assets')
    list_filter = ('cash_and_investments', 'clients_wallet', 'total_inventory', 'total_assets')

@admin.register(Passives)
class PassivesAdmin(admin.ModelAdmin):
    list_display = ('id', 'financial_obligation_cp', 'providers', 'unpaid_expenses',) 
    search_fields = ('financial_obligation_cp', 'providers', 'unpaid_expenses',)
    list_filter = ('financial_obligation_cp', 'providers', 'unpaid_expenses',)

@admin.register(Patrimony)
class PatrimonyAdmin(admin.ModelAdmin):
    list_display = ('id', 'payed_capital', 'sup_capital_prima', 'legal_reserve', 'periods_results', ) 
    search_fields = ('payed_capital', 'sup_capital_prima', 'legal_reserve')
    list_filter = ('payed_capital', 'sup_capital_prima', 'legal_reserve')

@admin.register(StateOfResult)
class StateOfResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'gross_sale', 'dtos_returns', 'net_sales', 'cost_of_sales', ) 
    search_fields = ('gross_sale', 'dtos_returns', 'net_sales', 'cost_of_sales',)
    list_filter = ('gross_sale', 'dtos_returns', 'net_sales', 'cost_of_sales',)

@admin.register(FinancialProfile)
class FinancialProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'period', 'periodRange', 'periodDays', 'periodStartDate', 'periodEndDate', 'balance', )
    search_fields = ('period', 'periodRange', 'periodDays',)
    list_filter = ('period', 'periodRange', 'periodDays',)

@admin.register(FinancialCentral)
class FinancialCentralAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'centralBalances', 'rating', ) 
    search_fields = ('client', 'centralBalances', 'rating',)
    list_filter = ('client', 'centralBalances', 'rating',)

@admin.register(Overview)
class OverviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'qualitativeOverview', 'financialAnalisis', ) 
    search_fields = ('client', 'qualitativeOverview', 'financialAnalisis',)
    list_filter = ('client', 'qualitativeOverview', 'financialAnalisis',)

@admin.register(LegalClient)
class LegalClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'typeClient', 'companyName', 'country', ) 
    search_fields = ('email', 'typeClient', 'companyName', 'country',)
    list_filter = ('email', 'typeClient', 'companyName', 'country',)

@admin.register(FinancialRelations)
class FinancialRelationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'amount', 'tax',)  
    search_fields = ('legalClient', 'name', 'amount', 'tax')
    list_filter = ('legalClient', 'name', 'amount', 'tax')

@admin.register(LegalClientContacts)
class LegalClientContactsAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'area', 'phone', 'email',) 
    search_fields = ('legalClient', 'name', 'area', 'phone', 'email',)
    list_filter = ('legalClient', 'name', 'area', 'phone', 'email',)

@admin.register(ManagementBoard)
class ManagementBoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'type', ) 
    search_fields = ('legalClient', 'name', 'type',)
    list_filter = ('legalClient', 'name', 'type',)

@admin.register(PartnersAndShareholders)
class PartnersAndShareholdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'documentNumber', 'percentage', ) 
    search_fields = ('legalClient', 'name', 'documentNumber', 'percentage',)
    list_filter = ('legalClient', 'name', 'documentNumber', 'percentage',)

@admin.register(PrincipalClients)
class PrincipalClientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'salePercentage', 'contactName', ) 
    search_fields = ('legalClient', 'name', 'salePercentage', 'contactName',)
    list_filter = ('legalClient', 'name', 'salePercentage', 'contactName',)

@admin.register(PrincipalCompetitors)
class PrincipalCompetitorsAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'percentage', ) 
    search_fields = ('legalClient', 'name', 'percentage')
    list_filter = ('legalClient', 'name', 'percentage',)

@admin.register(PrincipalProducts)
class PrincipalProductsAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'percentage', ) 
    search_fields = ('legalClient', 'name', 'percentage')
    list_filter = ('legalClient', 'name', 'percentage',)

@admin.register(PrincipalProviders)
class PrincipalProvidersAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'name', 'salePercentage', 'contactName', 'phone', ) 
    search_fields = ('legalClient', 'name', 'salePercentage', 'contactName', 'phone', )
    list_filter = ('legalClient', 'name', 'salePercentage', 'contactName', 'phone', )

@admin.register(NaturalClient)
class NaturalClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'firstName', 'lastName', 'email', 'phone', 'companyName', ) 
    search_fields = ('firstName', 'lastName', 'email', 'phone')
    list_filter = ('firstName', 'lastName', 'email', 'phone')

@admin.register(LegalClientDocuments)
class LegalClientDocumentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'legalClient', 'date', 'status', ) 
    search_fields = ('legalClient', 'date', 'status')
    list_filter = ('legalClient', 'date', 'status',)

@admin.register(NaturalClientDocuments)
class NaturalClientDocumentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'naturalClient', 'date', 'status', ) 
    search_fields = ('naturalClient', 'date', 'status',)
    list_filter = ('naturalClient', 'date', 'status',)