import logging
import hashlib


def generate_device_id_from_login(login: str) -> str:
    return hashlib.sha256(login.encode('utf-8')).hexdigest()[:21]


class SafeFormatDict(dict):
    def __missing__(self, key):
        logging.warning(f"Неизвестная переменная в шаблоне: {{{key}}}")
        return f"{{{key}}}"


def build_template_vars(payment) -> dict:
    metadata = payment.metadata or {}

    invoice_id = ""
    if payment.invoice_details and hasattr(payment.invoice_details, 'id'):
        invoice_id = payment.invoice_details.id or ""

    order_number = metadata.get("orderNumber") or metadata.get("dashboardInvoiceOriginalNumber") or ""
    customer_name = metadata.get("custName") or metadata.get("customerNumber") or ""

    return SafeFormatDict({
        "description": payment.description or payment.id,
        "id": payment.id,
        "payment_description": payment.description or "",
        "order_number": order_number,
        "invoice_id": invoice_id,
        "customer_name": customer_name,
        "amount": payment.amount.value,
        "merchant_customer_id": getattr(payment, 'merchant_customer_id', "") or "",
    })
