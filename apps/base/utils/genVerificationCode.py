# Utils
import random
# Models
from apps.report.api.models.sellOrder.index import SellOrder

def genVerificationCode():
    # Generate a random 3-digit verification code nad verify 
    # it's not already in use in sellOffer model fields approveCode and rejectCde

    # Generate a random 3-digit verification code
    code = random.randint(100, 999)

    # verify it's not already in use in sellOffer model fields approveCode and rejectCde
    while SellOrder.objects.filter(approveCode=code).exists() or SellOrder.objects.filter(rejectCode=code).exists():
        code = random.randint(100, 999)
    
    # return the code
    return code
