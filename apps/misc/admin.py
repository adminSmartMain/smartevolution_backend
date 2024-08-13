from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
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

class TypeCLientResource(resources.ModelResource):
    class Meta:
        model = TypeCLient
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class CityResource(resources.ModelResource):
    class Meta:
        model = City
        fields = ('id', 'description', 'department',)
        import_id_fields = ('id',)

class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class TypeIdentityResource(resources.ModelResource):
    class Meta:
        model = TypeIdentity
        fields = ('id', 'description', 'abbreviation',)
        import_id_fields = ('id',)

class BankResource(resources.ModelResource):
    class Meta:
        model = Bank
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class AccountTypeResource(resources.ModelResource):
    class Meta:
        model = AccountType
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class SectionResource(resources.ModelResource):
    class Meta:
        model = Section
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class CIIUResource(resources.ModelResource):
    class Meta:
        model = CIIU
        fields = ('id', 'section', 'activity', 'code',)
        import_id_fields = ('id',)

class ActivityResource(resources.ModelResource):
    class Meta:
        model = Activity
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class CountryResource(resources.ModelResource):
    class Meta:
        model = Country
        fields = ('id', 'name_en', 'name_es', 'code', 'src',)
        import_id_fields = ('id',)

class TypeBillResource(resources.ModelResource):
    class Meta:
        model = TypeBill
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class TypeOperationResource(resources.ModelResource):
    class Meta:
        model = TypeOperation
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class TypeEventResource(resources.ModelResource):
    class Meta:
        model = TypeEvent
        fields = ('id', 'code', 'description',)
        import_id_fields = ('id',)

class TypeReceiptResource(resources.ModelResource):
    class Meta:
        model = TypeReceipt
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class TypeExpenditureResource(resources.ModelResource):
    class Meta:
        model = TypeExpenditure
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class AccountingAccountResource(resources.ModelResource):
    class Meta:
        model = AccountingAccount
        fields = ('id', 'code', 'description', 'accountNumber',)
        import_id_fields = ('id',)

class TypePeriodResource(resources.ModelResource):
    class Meta:
        model = TypePeriod
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class PeriodRangeResource(resources.ModelResource):
    class Meta:
        model = PeriodRange
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class ReceiptStatusResource(resources.ModelResource):
    class Meta:
        model = ReceiptStatus
        fields = ('id', 'description',)
        import_id_fields = ('id',)

class FixesResource(resources.ModelResource):
    class Meta:
        model = Fixes
        fields = ('id', 'accountId', 'date', 'gmAmount',)
        import_id_fields = ('id',)

@admin.register(TypeCLient)
class TypeCLientAdmin(ImportExportModelAdmin):
    resource_class = TypeCLientResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(City)
class CityAdmin(ImportExportModelAdmin):
    resource_class = CityResource
    list_display = ('id', 'description', 'department')
    search_fields = ('description', 'department')
    list_filter = ('description', 'department')

@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    resource_class = DepartmentResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeIdentity)
class TypeIdentityAdmin(ImportExportModelAdmin):
    resource_class = TypeIdentityResource
    list_display = ('id', 'description', 'abbreviation')
    search_fields = ('description', 'abbreviation',)
    list_filter = ('description', 'abbreviation',)

@admin.register(Bank)
class BankAdmin(ImportExportModelAdmin):
    resource_class = BankResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(AccountType)
class AccountTypeAdmin(ImportExportModelAdmin):
    resource_class = AccountTypeResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(Section)
class SectionAdmin(ImportExportModelAdmin):
    resource_class = SectionResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(CIIU)
class CIIUAdmin(ImportExportModelAdmin):
    resource_class = CIIUResource
    list_display = ('id', 'section', 'activity', 'code')
    search_fields = ('section', 'activity', 'code')
    list_filter = ('section', 'activity', 'code')

@admin.register(Activity)
class ActivityAdmin(ImportExportModelAdmin):
    resource_class = ActivityResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
    resource_class = CountryResource
    list_display = ('id', 'name_en', 'name_es', 'code', 'src')
    search_fields = ('name_en', 'name_es', 'code', 'src')
    list_filter = ('name_en', 'name_es', 'code', 'src')

@admin.register(TypeBill)
class TypeBillAdmin(ImportExportModelAdmin):
    resource_class = TypeBillResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeOperation)
class TypeOperationAdmin(ImportExportModelAdmin):
    resource_class = TypeOperationResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeEvent)
class TypeEventAdmin(ImportExportModelAdmin):
    resource_class = TypeEventResource
    list_display = ('id', 'code', 'description')
    search_fields = ('code', 'description',)
    list_filter = ('code', 'description',)

@admin.register(TypeReceipt)
class TypeReceiptAdmin(ImportExportModelAdmin):
    resource_class = TypeReceiptResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(TypeExpenditure)
class TypeExpenditureAdmin(ImportExportModelAdmin):
    resource_class = TypeExpenditureResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(AccountingAccount)
class AccountingAccountAdmin(ImportExportModelAdmin):
    resource_class = AccountingAccountResource
    list_display = ('id', 'code', 'description', 'accountNumber')
    search_fields = ('code', 'description', 'accountNumber')
    list_filter = ('code', 'description', 'accountNumber')

@admin.register(TypePeriod)
class TypePeriodAdmin(ImportExportModelAdmin):
    resource_class = TypePeriodResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(PeriodRange)
class PeriodRangeAdmin(ImportExportModelAdmin):
    resource_class = PeriodRangeResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(ReceiptStatus)
class ReceiptStatusAdmin(ImportExportModelAdmin):
    resource_class = ReceiptStatusResource
    list_display = ('id', 'description')
    search_fields = ('description',)
    list_filter = ('description',)

@admin.register(Fixes)
class FixesAdmin(ImportExportModelAdmin):
    resource_class = FixesResource
    list_display = ('id', 'accountId', 'date', 'gmAmount')
    search_fields = ('accountId', 'date', 'gmAmount',)
    list_filter = ('accountId', 'date', 'gmAmount',)
