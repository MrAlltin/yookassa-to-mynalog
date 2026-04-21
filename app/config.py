import os
import time
from dotenv import load_dotenv

load_dotenv()

TZ = os.getenv("TZ")
if TZ:
    os.environ["TZ"] = TZ
    time.tzset()


def _read_secret(env_var: str, secret_name: str) -> str | None:
    """Читает значение из переменной окружения или из файла Docker Secret.
    Приоритет: переменная окружения → /run/secrets/<secret_name>.
    """
    value = os.getenv(env_var)
    if value:
        return value
    secret_path = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return None


YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_API_KEY = _read_secret("YOOKASSA_API_KEY", "yookassa_api_key")
MOY_NALOG_LOGIN = os.getenv("MOY_NALOG_LOGIN")
MOY_NALOG_PASSWORD = _read_secret("MOY_NALOG_PASSWORD", "moy_nalog_password")

DEVICE_ID = os.getenv("DEVICE_ID")
SYNC_START_DATE = os.getenv("SYNC_START_DATE")
INCOME_DESCRIPTION_TEMPLATE = os.getenv("INCOME_DESCRIPTION_TEMPLATE", "Платеж #{description}")
PAYMENT_TYPE = os.getenv("PAYMENT_TYPE", "ACCOUNT")
CRON_SCHEDULE = os.getenv("CRON_SCHEDULE", "0 */4 * * *")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_THREAD_ID = os.getenv("TELEGRAM_THREAD_ID")
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY")

def validate_config():
    required_vars = [
        ("YOOKASSA_SHOP_ID", YOOKASSA_SHOP_ID),
        ("YOOKASSA_API_KEY", YOOKASSA_API_KEY),
        ("MOY_NALOG_LOGIN", MOY_NALOG_LOGIN),
        ("MOY_NALOG_PASSWORD", MOY_NALOG_PASSWORD),
    ]

    missing = [var for var, val in required_vars if not val]
    if missing:
        raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}")

    if TELEGRAM_BOT_TOKEN and not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN задан, но TELEGRAM_CHAT_ID отсутствует.")
    if TELEGRAM_CHAT_ID and not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_CHAT_ID задан, но TELEGRAM_BOT_TOKEN отсутствует.")

    return True
