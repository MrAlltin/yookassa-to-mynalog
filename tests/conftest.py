import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock

# Добавляем app/ в путь, чтобы импортировать модули напрямую
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Мокаем config до импорта любых модулей приложения
config_mock = MagicMock()
config_mock.YOOKASSA_SHOP_ID = "test_shop"
config_mock.YOOKASSA_API_KEY = "test_key"
config_mock.MOY_NALOG_LOGIN = "123456789012"
config_mock.MOY_NALOG_PASSWORD = "test_password"
config_mock.DEVICE_ID = None
config_mock.SYNC_START_DATE = None
config_mock.INCOME_DESCRIPTION_TEMPLATE = "Платеж #{description}"
config_mock.PAYMENT_TYPE = "ACCOUNT"
config_mock.TELEGRAM_BOT_TOKEN = None
config_mock.TELEGRAM_CHAT_ID = None
config_mock.TELEGRAM_THREAD_ID = None
config_mock.TELEGRAM_PROXY = None
config_mock.validate_config = MagicMock(return_value=True)
sys.modules['config'] = config_mock


@pytest.fixture
def config_mod():
    return sys.modules['config']


def make_payment(
    payment_id="pay-uuid-001",
    amount="500.00",
    description="Тестовый платёж",
    created_at="2026-01-15T10:00:00Z",
    metadata=None,
):
    p = MagicMock()
    p.id = payment_id
    p.amount.value = amount
    p.description = description
    p.created_at = created_at
    p.metadata = metadata or {}
    p.invoice_details = None
    p.merchant_customer_id = ""
    return p


def make_refund(refund_id="ref-uuid-001", payment_id="pay-uuid-001", created_at="2026-01-15T11:00:00Z"):
    r = MagicMock()
    r.id = refund_id
    r.payment_id = payment_id
    r.created_at = created_at
    return r
