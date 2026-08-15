import traceback
import logging
from datetime import date, datetime
from decimal import Decimal
import uuid

from apps.operation.api.models.index import OperationLog
from apps.base.utils.index import gen_uuid

logger = logging.getLogger(__name__)


def _make_json_safe(value):
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, uuid.UUID):
        return str(value)

    if isinstance(value, dict):
        return {str(k): _make_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_make_json_safe(v) for v in value]

    return str(value)


def create_operation_log(
    *,
    source,
    action,
    status,
    message,
    op_id=None,
    pre_operation=None,
    request_payload=None,
    response_payload=None,
    error_type=None,
    error_detail=None,
    stack_trace=None,
    row_index=None,
    bill_code=None,
    bill_id_ref=None,
    extra_data=None,
    user=None,
):
    try:
        OperationLog.objects.create(
            id=gen_uuid(),  # <- ESTE ES EL FIX CLAVE
            opId=op_id,
            pre_operation=pre_operation,
            source=source,
            action=action,
            status=status,
            message=message,
            error_type=error_type,
            error_detail=error_detail,
            stack_trace=stack_trace,
            row_index=row_index,
            bill_code=_make_json_safe(bill_code),
            bill_id_ref=_make_json_safe(bill_id_ref),
            request_payload=_make_json_safe(request_payload),
            response_payload=_make_json_safe(response_payload),
            extra_data=_make_json_safe(extra_data),
            user_email=getattr(user, "email", None) if user else None,
            user_id_ref=str(getattr(user, "id", "")) if user else None,
        )
    except Exception as e:
        logger.exception(f"Error guardando OperationLog: {str(e)}")


def create_exception_log(
    *,
    source,
    action,
    exc,
    message,
    op_id=None,
    pre_operation=None,
    request_payload=None,
    row_index=None,
    bill_code=None,
    bill_id_ref=None,
    extra_data=None,
    user=None,
):
    create_operation_log(
        source=source,
        action=action,
        status="ERROR",
        message=message,
        op_id=op_id,
        pre_operation=pre_operation,
        request_payload=request_payload,
        error_type=exc.__class__.__name__,
        error_detail=str(exc),
        stack_trace=traceback.format_exc(),
        row_index=row_index,
        bill_code=bill_code,
        bill_id_ref=bill_id_ref,
        extra_data=extra_data,
        user=user,
    )