from django.db.models import Max
from apps.client.models import Client, Account, Broker, RiskProfile
from apps.operation.models import PreOperation
from apps.bill.models import Bill


class UploadExcelReferenceResolver:
    def resolve(self, parsed_rows):
        emitter_ids = {str(r["emitter_id"]) for r in parsed_rows if r.get("emitter_id")}
        payer_ids = {str(r["payer_id"]) for r in parsed_rows if r.get("payer_id")}
        investor_ids = {str(r["investor_id"]) for r in parsed_rows if r.get("investor_id")}
        bill_ids = {str(r["bill_id"]) for r in parsed_rows if r.get("bill_id")}
        emitter_broker_ids = {
            str(r["emitter_broker_id"])
            for r in parsed_rows
            if r.get("emitter_broker_id")
        }
        account_numbers = {
            str(r["investor_account"]).strip()
            for r in parsed_rows
            if r.get("investor_account")
        }

        clients = Client.objects.filter(id__in=(emitter_ids | payer_ids | investor_ids))
        bills = Bill.objects.filter(id__in=bill_ids)
        brokers = Broker.objects.filter(id__in=emitter_broker_ids)
        accounts = Account.objects.filter(account_number__in=account_numbers)

        accounts_by_number = {
            str(a.account_number).strip(): a
            for a in accounts
            if a.account_number
        }

        risk_profiles = RiskProfile.objects.filter(client_id__in=investor_ids)
        risk_profile_by_client_id = {
            str(rp.client_id): rp
            for rp in risk_profiles
            if rp.client_id
        }

        fractions_by_bill = (
            PreOperation.objects
            .filter(bill_id__in=bill_ids)
            .values("bill_id")
            .annotate(max_fraction=Max("billFraction"))
        )

        max_fraction_map = {
            str(item["bill_id"]): int(item["max_fraction"] or 0)
            for item in fractions_by_bill
        }

        next_fraction_by_bill = {}
        for bill_id in bill_ids:
            max_fraction = max_fraction_map.get(str(bill_id), 0)
            next_fraction_by_bill[str(bill_id)] = max_fraction + 1 if max_fraction > 0 else 1

        investor_broker_by_investor_id = {}
        for client in clients:
            client_id = str(client.id)
            if client_id in investor_ids:
                broker_id = getattr(client, "broker_id", None)
                broker_obj = getattr(client, "broker", None)
                investor_broker_by_investor_id[client_id] = {
                    "broker_id": str(broker_id) if broker_id else None,
                    "broker_name": str(broker_obj) if broker_obj else "",
                }

        return {
            "clients_by_id": {str(c.id): c for c in clients},
            "bills_by_id": {str(b.id): b for b in bills},
            "brokers_by_id": {str(b.id): b for b in brokers},
            "accounts_by_number": accounts_by_number,
            "risk_profile_by_client_id": risk_profile_by_client_id,
            "next_fraction_by_bill": next_fraction_by_bill,
            "investor_broker_by_investor_id": investor_broker_by_investor_id,
        }