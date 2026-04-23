from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


def make_api():
    from nalog_api import MoyNalogAPI
    with patch("nalog_api.config") as cfg:
        cfg.DEVICE_ID = None
        cfg.PAYMENT_TYPE = "WIRE"
        api = MoyNalogAPI("123456789012", "test_password")
    api.client = AsyncMock()
    return api


def make_response(status_code, json_data=None, text=""):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


class TestAuthenticate:
    @pytest.mark.asyncio
    async def test_success_stores_token(self):
        api = make_api()
        api.client.post = AsyncMock(return_value=make_response(200, {"token": "tok-abc"}))

        result = await api.authenticate()

        assert result is True
        assert api.token == "tok-abc"

    @pytest.mark.asyncio
    async def test_raises_on_non_200(self):
        """tenacity исчерпывает 3 попытки и бросает RetryError, внутри которого HTTP 401."""
        from tenacity import RetryError
        api = make_api()
        api.client.post = AsyncMock(return_value=make_response(401, text="Unauthorized"))

        with pytest.raises(RetryError) as exc_info:
            await api.authenticate()
        assert "HTTP 401" in str(exc_info.value.last_attempt.exception())

    @pytest.mark.asyncio
    async def test_raises_when_no_token_in_response(self):
        """tenacity исчерпывает 3 попытки и бросает RetryError, внутри которого сообщение о токене."""
        from tenacity import RetryError
        api = make_api()
        api.client.post = AsyncMock(return_value=make_response(200, {"token": None}))

        with pytest.raises(RetryError) as exc_info:
            await api.authenticate()
        assert "токен" in str(exc_info.value.last_attempt.exception())

    @pytest.mark.asyncio
    async def test_sets_authorization_header(self):
        api = make_api()
        api.client.post = AsyncMock(return_value=make_response(200, {"token": "tok-xyz"}))
        api.client.headers = {}

        await api.authenticate()

        assert api.client.headers.get("Authorization") == "Bearer tok-xyz"


class TestAddIncome:
    @pytest.mark.asyncio
    async def test_returns_receipt_uuid_on_success(self):
        api = make_api()
        api.token = "tok-abc"
        api.client.post = AsyncMock(return_value=make_response(
            200, {"approvedReceiptUuid": "receipt-001"}
        ))
        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        result = await api.add_income("Услуга", 500.0, date)

        assert result == "receipt-001"

    @pytest.mark.asyncio
    async def test_returns_none_on_error_status(self):
        api = make_api()
        api.token = "tok-abc"
        api.client.post = AsyncMock(return_value=make_response(500, text="Server Error"))
        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        result = await api.add_income("Услуга", 500.0, date)

        assert result is None

    @pytest.mark.asyncio
    async def test_reauthenticates_on_401(self):
        api = make_api()
        api.token = "old-token"
        api.authenticate = AsyncMock()

        resp_401 = make_response(401)
        resp_ok = make_response(200, {"approvedReceiptUuid": "receipt-002"})
        api.client.post = AsyncMock(side_effect=[resp_401, resp_ok])

        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = await api.add_income("Услуга", 500.0, date)

        api.authenticate.assert_called_once()
        assert result == "receipt-002"

    @pytest.mark.asyncio
    async def test_authenticates_if_no_token(self):
        api = make_api()
        api.token = None
        api.authenticate = AsyncMock(side_effect=lambda: setattr(api, "token", "new-tok") or True)
        api.client.post = AsyncMock(return_value=make_response(200, {"approvedReceiptUuid": "receipt-003"}))

        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = await api.add_income("Услуга", 500.0, date)

        api.authenticate.assert_called_once()
        assert result == "receipt-003"

    @pytest.mark.asyncio
    async def test_payload_uses_payment_type_from_config(self):
        api = make_api()
        api.token = "tok-abc"
        captured = {}

        async def capture_post(url, json=None, headers=None):
            captured["payload"] = json
            return make_response(200, {"approvedReceiptUuid": "r-001"})

        api.client.post = capture_post
        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        with patch("nalog_api.config") as cfg:
            cfg.PAYMENT_TYPE = "WIRE"
            await api.add_income("Услуга", 500.0, date)

        assert captured["payload"]["paymentType"] == "ACCOUNT"


class TestCancelIncome:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        api = make_api()
        api.token = "tok-abc"
        api.client.post = AsyncMock(return_value=make_response(200))

        result = await api.cancel_income("receipt-001")

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_error_status(self):
        api = make_api()
        api.token = "tok-abc"
        api.client.post = AsyncMock(return_value=make_response(400, text="Bad Request"))

        result = await api.cancel_income("receipt-001")

        assert result is False

    @pytest.mark.asyncio
    async def test_reauthenticates_on_401(self):
        api = make_api()
        api.token = "old-token"
        api.authenticate = AsyncMock()

        resp_401 = make_response(401)
        resp_ok = make_response(200)
        api.client.post = AsyncMock(side_effect=[resp_401, resp_ok])

        result = await api.cancel_income("receipt-001")

        api.authenticate.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_payload_contains_receipt_uuid(self):
        api = make_api()
        api.token = "tok-abc"
        captured = {}

        async def capture_post(url, json=None, headers=None):
            captured["payload"] = json
            return make_response(200)

        api.client.post = capture_post

        await api.cancel_income("receipt-xyz")

        assert captured["payload"]["receiptUuid"] == "receipt-xyz"
        assert captured["payload"]["comment"] == "Возврат средств"


class TestFindIncome:
    def _make_income(self, name, amount, receipt_uuid, cancelled=False, payment_id_in_name=False):
        income = {
            "name": name,
            "totalAmount": str(amount),
            "approvedReceiptUuid": receipt_uuid,
            "cancellationInfo": {"reason": "refund"} if cancelled else None,
        }
        return income

    @pytest.mark.asyncio
    async def test_finds_by_payment_id_in_name(self):
        api = make_api()
        api.token = "tok-abc"
        payment_id = "pay-uuid-001"
        income = self._make_income(f"Платеж {payment_id}", 500.0, "receipt-001")
        api.client.get = AsyncMock(return_value=make_response(200, {"content": [income]}))

        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = await api.find_income("Платеж pay-uuid-001", 500.0, payment_id, date)

        assert result == "receipt-001"

    @pytest.mark.asyncio
    async def test_finds_by_name_and_amount_fallback(self):
        api = make_api()
        api.token = "tok-abc"
        income = self._make_income("Услуга X", 300.0, "receipt-002")
        api.client.get = AsyncMock(return_value=make_response(200, {"content": [income]}))

        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = await api.find_income("Услуга X", 300.0, "other-id", date)

        assert result == "receipt-002"

    @pytest.mark.asyncio
    async def test_skips_cancelled_incomes(self):
        api = make_api()
        api.token = "tok-abc"
        cancelled = self._make_income("Услуга X", 300.0, "receipt-cancelled", cancelled=True)
        api.client.get = AsyncMock(return_value=make_response(200, {"content": [cancelled]}))

        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = await api.find_income("Услуга X", 300.0, "pay-001", date)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        api = make_api()
        api.token = "tok-abc"
        api.client.get = AsyncMock(return_value=make_response(200, {"content": []}))

        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = await api.find_income("Несуществующая услуга", 999.0, "pay-001", date)

        assert result is None

    @pytest.mark.asyncio
    async def test_search_window_is_narrow(self):
        """Запрос к API должен использовать окно ±1ч от даты платежа, а не 7 дней."""
        api = make_api()
        api.token = "tok-abc"
        captured_url = {}

        async def capture_get(url, headers=None):
            captured_url["url"] = url
            return make_response(200, {"content": []})

        api.client.get = capture_get
        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        await api.find_income("Услуга", 100.0, "pay-001", date)

        url = captured_url["url"]
        # from должен быть около 09:00, to — около 11:00
        assert "2026-01-15T09" in url
        assert "2026-01-15T11" in url

    @pytest.mark.asyncio
    async def test_reauthenticates_on_401(self):
        api = make_api()
        api.token = "tok-abc"
        api.authenticate = AsyncMock()

        resp_401 = make_response(401)
        resp_ok = make_response(200, {"content": []})
        api.client.get = AsyncMock(side_effect=[resp_401, resp_ok])

        date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        await api.find_income("Услуга", 100.0, "pay-001", date)

        api.authenticate.assert_called_once()
