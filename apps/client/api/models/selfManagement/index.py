from django.db import models

# Relations
from apps.misc.models import (City, TypeIdentity, TypeCLient, CIIU, Country, 
                              Department, AccountType, Bank)
from apps.base.models import BaseModel



class NaturalClient(BaseModel):
    firstName = models.CharField(max_length=255)
    lastName  = models.CharField(max_length=255)
    birthDate = models.DateField()
    email = models.EmailField(max_length=255, unique=False, null=True, blank=True, error_messages={'unique': 'Ya existe un cliente con este correo'})
    mainEmail = models.EmailField(max_length=255, unique=False, null=False, blank=True, error_messages={'unique': 'Ya existe un cliente con este correo'})
    typeVinculation = models.IntegerField(default=0)
    typeDocument = models.ForeignKey(TypeIdentity, on_delete=models.CASCADE)
    documentNumber = models.CharField(max_length=255, unique=False, error_messages={'unique': 'Ya existe un cliente con este documento'})
    dateOfExpedition = models.DateField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    homePhone = models.CharField(max_length=255, null=True, blank=True)
    companyName = models.CharField(max_length=255, null=True, blank=True)
    activity = models.IntegerField(null=True, blank=True)
    activityType = models.ForeignKey(CIIU, on_delete=models.CASCADE, related_name='natural_client_activity_type', null=True, blank=True)
    product = models.CharField(max_length=255, null=True, blank=True)
    profession = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    companyPhone = models.CharField(max_length=255, null=True, blank=True)
    companyDepartment = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='natural_client_company_department', null=True, blank=True)
    companyCity = models.ForeignKey(City, on_delete=models.CASCADE, related_name='natural_client_company_city', null=True, blank=True)
    companyAddress = models.CharField(max_length=255, null=True, blank=True)
    ciiu = models.ForeignKey(CIIU, on_delete=models.CASCADE, null=True, blank=True)
    secondaryCiiu = models.ForeignKey(CIIU, on_delete=models.CASCADE, related_name='natural_client_secondary_ciiu', null=True, blank=True)
    typeProducts = models.CharField(max_length=255, null=True, blank=True)
    mensualIncome = models.CharField(max_length=255, null=True, blank=True)
    mensualExpenses = models.CharField(max_length=255, null=True, blank=True)
    assets = models.CharField(max_length=255, null=True, blank=True)
    passives = models.CharField(max_length=255, null=True, blank=True)
    patrimony = models.CharField(max_length=255, null=True, blank=True)
    otherIncome = models.CharField(max_length=255, null=True, blank=True)
    conceptOtherIncome = models.CharField(max_length=255, null=True, blank=True)
    managePublicResources = models.BooleanField(default=False)
    publicRecognition = models.BooleanField(default=False)
    publicPersonRecognition = models.BooleanField(default=False)
    publicPersonRecognitionDescription = models.CharField(max_length=255, null=True, blank=True)
    foreignTax = models.BooleanField(default=False)
    foreignTaxDescription = models.CharField(max_length=255, null=True, blank=True)
    referenceFirstName = models.CharField(max_length=255, null=True, blank=True)
    referenceLastName = models.CharField(max_length=255, null=True, blank=True)
    referenceCompany = models.CharField(max_length=255, null=True, blank=True)
    referencePhone = models.CharField(max_length=255, null=True, blank=True)
    referenceDepartment = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='natural_client_reference_department', null=True, blank=True)
    referenceCity = models.ForeignKey(City, on_delete=models.CASCADE, related_name='natural_client_reference_city', null=True, blank=True)
    referenceBank = models.CharField(max_length=255, null=True, blank=True)
    referenceBankPhone = models.CharField(max_length=255, null=True, blank=True)
    referenceBankProduct = models.CharField(max_length=255, null=True, blank=True)
    referenceBankDepartment = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='natural_client_reference_bank_department', null=True, blank=True)
    referenceBankCity = models.ForeignKey(City, on_delete=models.CASCADE, related_name='natural_client_reference_bank_city', null=True, blank=True)
    termsAndConditions = models.BooleanField(default=False)
    documentFile = models.FileField(upload_to='documents/', null=True, blank=True)
    rentDeclarationFile = models.FileField(upload_to='documents/', null=True, blank=True)
    bankCertificationFile = models.FileField(upload_to='documents/', null=True, blank=True)
    status = models.IntegerField(default=0)

    class Meta:
        db_table = 'naturalClient'
        verbose_name = 'naturalClient'
        verbose_name_plural = 'naturalClient'
        ordering = ['-created_at']


class LegalClient(BaseModel):
    email = models.EmailField(max_length=255, unique=False, error_messages={'unique': 'Ya existe un cliente con este correo'})
    typeVinculation = models.IntegerField(default=0)
    typeClient = models.ForeignKey(TypeCLient, on_delete=models.CASCADE)
    companyName = models.CharField(max_length=255)
    nit = models.CharField(max_length=255)
    ciiu = models.ForeignKey(CIIU, on_delete=models.CASCADE)
    verificationDigit = models.CharField(max_length=255)
    dateOfConstitution = models.DateField()
    principalAddress = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True, related_name='legal_client_country_of_birth')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='legal_client_department')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='legal_client_city')
    companyEmail = models.EmailField(max_length=255)
    companyPhone = models.CharField(max_length=255)
    socialObject = models.CharField(max_length=255)
    presenceInOtherCities = models.CharField(max_length=255)
    numberOfEmployees = models.CharField(max_length=255)
    greatContributor = models.BooleanField(default=False)
    selfRetainer = models.BooleanField(default=False)
    retIca = models.FloatField(default=0)
    retFte = models.FloatField(default=0)
    legalRepresentativeName = models.CharField(max_length=255)
    legalRepresentativeLastName = models.CharField(max_length=255)
    legalRepresentativeTypeDocument = models.ForeignKey(TypeIdentity, on_delete=models.CASCADE)
    legalRepresentativeDocumentNumber =  models.CharField(max_length=255)
    legalRepresentativeCountry = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='legal_client_country')
    legalRepresentativeBirthDate = models.DateField()
    legalRepresentativeAddress = models.CharField(max_length=255)
    legalRepresentativeDepartment = models.ForeignKey(Department, on_delete=models.CASCADE)
    legalRepresentativeCity = models.ForeignKey(City, on_delete=models.CASCADE)
    legalRepresentativePhone = models.CharField(max_length=255)
    legalRepresentativePersonalPhone = models.CharField(max_length=255)
    legalRepresentativeEmail = models.EmailField(max_length=255)
    legalRepresentativePosition = models.CharField(max_length=255)
    attributionsAndLimitations = models.CharField(max_length=255)
    internationalOperations = models.BooleanField(default=False)
    internationalOperationsDescription = models.CharField(max_length=255, null=True, blank=True)
    foreignAccount = models.BooleanField(default=False)
    typeForeignAccount = models.CharField(max_length=255, null=True, blank=True)
    foreignAccountNumber = models.CharField(max_length=255, null=True, blank=True)
    foreignAccountInstitution = models.CharField(max_length=255, null=True, blank=True)
    foreignAccountCountry = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    foreignAccountCurrency = models.CharField(max_length=255, null=True, blank=True)
    businessSeasonality = models.CharField(max_length=255)
    installedCapacityVsUsedCapacity = models.CharField(max_length=255)
    futureProjects = models.CharField(max_length=255)
    payrollBank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='payrollBank')
    acquisitionsBank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='acquisitionsBank')
    publicResources = models.BooleanField(default=False)
    publicPower = models.BooleanField(default=False)
    publicAcknowledgment = models.BooleanField(default=False)
    publicPersonLink = models.BooleanField(default=False)
    publicPersonLinkDescription = models.CharField(max_length=255)
    foreignCountryTax = models.BooleanField(default=False)
    foreignCountryTaxDescription = models.CharField(max_length=255, null=True, blank=True)
    occupationalRiskPolicy = models.BooleanField(default=False)
    assetLaunderingPolicy = models.BooleanField(default=False)
    laftRiskPolicy = models.BooleanField(default=False)
    laftAnualDictamen = models.BooleanField(default=False)
    laftInternalAuditor = models.BooleanField(default=False)
    termsAndConditions = models.BooleanField(default=False)
    bankCertification = models.FileField(upload_to='clients/bankCertification', null=True, blank=True)
    legalRepresentationCertification = models.FileField(upload_to='clients/legalRepresentationCertification', null=True, blank=True)
    financialStatementsCertification = models.FileField(upload_to='clients/financialStatementsCertification', null=True, blank=True)
    rentDeclaration = models.FileField(upload_to='clients/rentDeclaration', null=True, blank=True)
    dianAccountState = models.FileField(upload_to='clients/dianAccountState', null=True, blank=True)
    rutFile = models.FileField(upload_to='clients/rutFile', null=True, blank=True)
    legalRepresentativeIdFile = models.FileField(upload_to='clients/legalRepresentativeIdFile', null=True, blank=True)
    legalRepresentativeDocumentFile = models.FileField(upload_to='clients/legalRepresentativeDocumentFile', null=True, blank=True)
    descriptionAndInformation = models.CharField(max_length=255, null=True, blank=True)
    shareholdingStructure = models.FileField(upload_to='clients/shareholdingStructure', null=True, blank=True)
    status = models.IntegerField(default=0)

    class Meta:
        db_table = 'legalClient'
        verbose_name = 'legalClient'
        verbose_name_plural = 'legalClient'
        ordering = ['-created_at']


class ManagementBoard(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)

class PartnersAndShareholders(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    documentNumber = models.CharField(max_length=255)
    percentage = models.FloatField(default=0)


class PrincipalProducts(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    percentage = models.FloatField(default=0)

class PrincipalClients(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    deadline = models.CharField(max_length=255)
    salePercentage = models.FloatField(default=0)
    contactName = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)


class PrincipalProviders(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    deadline = models.CharField(max_length=255)
    salePercentage = models.FloatField(default=0)
    contactName = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)

class PrincipalCompetitors(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    percentage = models.FloatField(default=0)

class FinancialRelations(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.FloatField(default=0)
    deadline = models.CharField(max_length=255)
    tax = models.CharField(max_length=255)

class LegalClientContacts(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    area = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)

class LegalClientDocuments(BaseModel):
    legalClient = models.ForeignKey(LegalClient, on_delete=models.CASCADE)
    url         = models.CharField(max_length=255, null=True, blank=True)
    date        = models.DateField(null=True, blank=True)
    idRequest   = models.CharField(max_length=255, null=True, blank=True)
    idSignature = models.CharField(max_length=255, null=True, blank=True)
    status      = models.IntegerField(default=0)
    signStatus  = models.IntegerField(default=0)


class NaturalClientDocuments(BaseModel):
    naturalClient = models.ForeignKey(NaturalClient, on_delete=models.CASCADE)
    url           = models.CharField(max_length=255, null=True, blank=True)
    date          = models.DateField(null=True, blank=True)
    idRequest     = models.CharField(max_length=255, null=True, blank=True)
    idSignature   = models.CharField(max_length=255, null=True, blank=True)
    status        = models.IntegerField(default=0)
    signStatus    = models.IntegerField(default=0)