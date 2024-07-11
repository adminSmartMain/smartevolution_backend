from random import randint
from apps.client.api.models.account.index import Account


def genAccountNumber():
    valid = False
    while valid == False:
        result_str = str(randint(0, 999999999999))
        if Account.objects.filter(account_number=result_str).exists():
            valid = False
        else:
            valid = True

    return result_str

def random_with_N_digits(n):
    valid = False
    range_start = 10**(n-1)
    range_end = (10**n)-1
    generatedNumber = str(randint(range_start, range_end))

    while valid == False:
        if Account.objects.filter(account_number=generatedNumber).exists():
            valid = False
        else:
            valid = True
    
    return generatedNumber