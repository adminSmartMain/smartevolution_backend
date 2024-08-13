from django.contrib import admin
from .api.models.index import (
    TypeCLient,
    City,
    Department,
    TypeIdentity,
    Bank,
    AccountType,
    Section,
    CIIU,
    Activity,
    Country,
    TypeBill,
    TypeOperation,
    TypeEvent,
    TypeReceipt,
    TypeExpenditure,
    AccountingAccount,
    TypePeriod,
    PeriodRange,
    ReceiptStatus,
    Fixes
)



@admin.register(TypeCLient)
class TypeCLientAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'department')
    search_fields = ('description', 'department')
    list_filter = ('description', 'department')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeIdentity)
class TypeIdentityAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'abbreviation')
    search_fields = ('description', 'abbreviation',)
    list_filter = ('description', 'abbreviation',)

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(CIIU)
class CIIUAdmin(admin.ModelAdmin):
    list_display = ('id', 'section', 'activity', 'code')
    search_fields = ('section', 'activity', 'code')
    list_filter = ('section', 'activity', 'code')

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_en', 'name_es', 'code', 'src')
    search_fields = ('name_en', 'name_es', 'code', 'src')
    list_filter = ('name_en', 'name_es', 'code', 'src')

@admin.register(TypeBill)
class TypeBillAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeOperation)
class TypeOperationAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeEvent)
class TypeEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'description')
    search_fields = ('code', 'description',)
    list_filter = ('code', 'description',)

@admin.register(TypeReceipt)
class TypeReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeExpenditure)
class TypeExpenditureAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(AccountingAccount)
class AccountingAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'description', 'accountNumber')
    search_fields = ('code', 'description', 'accountNumber')
    list_filter = ('code', 'description', 'accountNumber')

@admin.register(TypePeriod)
class TypePeriodAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(PeriodRange)
class PeriodRangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(ReceiptStatus)
class ReceiptStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(Fixes)
class FixesAdmin(admin.ModelAdmin):
    list_display = ('id', 'accountId', 'date', 'gmAmount')
    search_fields = ('accountId', 'date', 'gmAmount',)
    list_filter = ('accountId', 'date', 'gmAmount',)