from django.utils import timezone
from apps.client.models import Account, AccountBalanceHistory

def log_balance_change(account, old_balance, new_balance, amount_changed, operation_type, operation_id, description):
    """
    Registra un cambio en el balance de una cuenta.
    
    :param account: Instancia del modelo Account.
    :param old_balance: Valor anterior del balance.
    :param new_balance: Valor nuevo del balance.
    :param operation_type: Tipo de operación realizada.
    """
    
    AccountBalanceHistory.objects.create(
        account=account,
        old_balance=old_balance,
        new_balance=new_balance,
        amount_changed=amount_changed,
        operation_type=operation_type,
        operation_id=operation_id,
        description=description
    )
