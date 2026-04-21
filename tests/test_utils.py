import pytest
from conftest import make_payment
from utils import generate_device_id_from_login, SafeFormatDict, build_template_vars


class TestGenerateDeviceId:
    def test_length_is_21(self):
        result = generate_device_id_from_login("123456789012")
        assert len(result) == 21

    def test_same_input_same_output(self):
        assert generate_device_id_from_login("123456789012") == generate_device_id_from_login("123456789012")

    def test_different_inputs_different_output(self):
        assert generate_device_id_from_login("111111111111") != generate_device_id_from_login("222222222222")

    def test_only_hex_chars(self):
        result = generate_device_id_from_login("123456789012")
        assert all(c in "0123456789abcdef" for c in result)


class TestSafeFormatDict:
    def test_existing_key_returns_value(self):
        d = SafeFormatDict({"name": "Иван"})
        assert d["name"] == "Иван"

    def test_missing_key_returns_placeholder(self):
        d = SafeFormatDict()
        assert d["unknown_key"] == "{unknown_key}"

    def test_format_map_with_missing_key(self):
        result = "Платеж {description} от {unknown}".format_map(SafeFormatDict({"description": "тест"}))
        assert result == "Платеж тест от {unknown}"


class TestBuildTemplateVars:
    def test_basic_fields(self):
        payment = make_payment(payment_id="abc-123", amount="1000.00", description="Услуга")
        result = build_template_vars(payment)
        assert result["id"] == "abc-123"
        assert result["amount"] == "1000.00"
        assert result["description"] == "Услуга"
        assert result["payment_description"] == "Услуга"

    def test_description_fallback_to_id(self):
        payment = make_payment(payment_id="abc-123", description=None)
        result = build_template_vars(payment)
        assert result["description"] == "abc-123"
        assert result["payment_description"] == ""

    def test_order_number_from_metadata(self):
        payment = make_payment(metadata={"orderNumber": "1234-5"})
        result = build_template_vars(payment)
        assert result["order_number"] == "1234-5"

    def test_order_number_fallback_key(self):
        payment = make_payment(metadata={"dashboardInvoiceOriginalNumber": "9999"})
        result = build_template_vars(payment)
        assert result["order_number"] == "9999"

    def test_customer_name_from_metadata(self):
        payment = make_payment(metadata={"custName": "ООО Ромашка"})
        result = build_template_vars(payment)
        assert result["customer_name"] == "ООО Ромашка"

    def test_empty_metadata(self):
        payment = make_payment(metadata={})
        result = build_template_vars(payment)
        assert result["order_number"] == ""
        assert result["customer_name"] == ""
        assert result["invoice_id"] == ""

    def test_invoice_id_from_invoice_details(self):
        from unittest.mock import MagicMock
        payment = make_payment()
        payment.invoice_details = MagicMock()
        payment.invoice_details.id = "inv-777"
        result = build_template_vars(payment)
        assert result["invoice_id"] == "inv-777"

    def test_returns_safe_format_dict(self):
        payment = make_payment()
        result = build_template_vars(payment)
        assert isinstance(result, SafeFormatDict)
        # Неизвестная переменная не бросает KeyError
        assert result["nonexistent"] == "{nonexistent}"
