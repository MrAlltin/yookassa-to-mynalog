<h1 align=center>Авто-Синхрон чеков из <code>ЮKassa</code> в <code>Мой Налог</code> для самозанятых (НПД)</h1>

> **Автоматическая синхронизация** платежей из личного кабинета ЮKassa в приложение "Мой Налог"

<p align=center>Данный репозиторий был создан и поддерживается в связи с тем, что <b>ЮKassa</b> остановили свой сервис авто-отправки чеков в "Мой Налог"</p>

---

## 🚀 Возможности

- ✅ Автоматическая синхронизация платежей при запуске контейнера
- ✅ Регулярное выполнение по расписанию (настраивается через .env)
- ✅ Валидация конфигурации при старте
- ✅ Автоматические повторы при сбоях сети
- ✅ Сохранение состояния синхронизации
- ✅ Подробное логирование

## 📋 Требования

- Docker
- Учетные данные ЮKassa (Shop ID + API ключ)
- Учетные данные Мой Налог (логин + пароль)

---

## 🔧 Установка

### 1. Устанавливаем Docker
```bash
sudo curl -fsSL https://get.docker.com | sh
```

### 2. Создаем папку `/opt/yookassa-to-mynalog` и переходим в нее
```bash
mkdir /opt/yookassa-to-mynalog && cd /opt/yookassa-to-mynalog
```

### 3. Скачиваем файлы `.env.example` (его сразу ренеймим в `.env`) и `docker-compose.yml`
```bash
wget -O .env https://raw.githubusercontent.com/grnfls709/yookassa-to-mynalog/refs/heads/master/.env.example && \
wget -O docker-compose.yml https://raw.githubusercontent.com/grnfls709/yookassa-to-mynalog/refs/heads/master/docker-compose.yml
```

### 4. Заполняем файл `.env` необходимыми значениями (см раздел "Конфигурация")
```bash
nano .env
```

## ⚙️ Конфигурация

### Обязательные переменные

| Переменная | Описание |
|-----------|---------|
| `YOOKASSA_SHOP_ID` | ID магазина в ЮKassa |
| `YOOKASSA_API_KEY` | API ключ ЮKassa |
| `MOY_NALOG_LOGIN` | ИНН в Мой Налог |
| `MOY_NALOG_PASSWORD` | Пароль в Мой Налог |

### Опциональные переменные

| Переменная | По умолчанию | Описание |
|-----------|:----------:|---------|
| `DEVICE_ID` | Генерация хеша из ИНН (21 символ) | Специальный ID, используемый для авторизации в "Мой Налог" |
| `SYNC_START_DATE` | -24ч | Дата начала синхронизации (YYYY-MM-DD) |
| `INCOME_DESCRIPTION_TEMPLATE` | `Платеж #{description}` | Шаблон описания дохода |
| `CRON_SCHEDULE` | `0 */4 * * *` | Расписание cron (каждые 4 часа) |

### Примеры CRON_SCHEDULE

```env
CRON_SCHEDULE='0 * * * *'        # каждый час
CRON_SCHEDULE='0 */6 * * *'      # каждые 6 часов
CRON_SCHEDULE='0 12 * * *'       # один раз в день в 12:00
CRON_SCHEDULE='*/30 * * * *'     # каждые 30 минут
CRON_SCHEDULE='0 0 * * 0'        # один раз в неделю в воскресенье
```

**Формат cron:** `минуты часы дни_месяца месяцы дни_недели`

## 🚀 Запуск

### Первый запуск
```bash
cd /opt/yookassa-to-mynalog && docker compose up -d
```

### Проверка логов
```bash
cd /opt/yookassa-to-mynalog && docker compose logs -f -t
```

### Остановка
```bash
cd /opt/yookassa-to-mynalog && docker compose down
```

### Перезагрузка
```bash
cd /opt/yookassa-to-mynalog && docker compose down && docker compose up -d
```

---

## 📊 Структура логов

```
2026-01-21 12:00:00,123 - INFO - Начало синхронизации...
2026-01-21 12:00:01,456 - INFO - ✓ Успешная авторизация в Мой Налог.
2026-01-21 12:00:02,789 - INFO - ✓ Найдено новых платежей: 3
2026-01-21 12:00:03,012 - INFO - ✓ Доход успешно зарегистрирован: 500 руб. за 'Платеж #12345'
...
2026-01-21 12:00:05,000 - INFO - Результат: успешно=3, ошибок=0
2026-01-21 12:00:05,001 - INFO - Синхронизация завершена.
```

---

## 💡 Обновление ПО

### 1. Переходим в нашу папку
```bash
cd /opt/yookassa-to-mynalog
```

### 2. Останавливаем контейнер
```bash
docker compose down
```

### 3. Скачиваем новый образ
```bash
docker compose pull
```

### 4. Запускаем контейнер и смотрим логи после запуска новой версии
```bash
docker compose up -d && docker compose logs -f -t
```

---

> **Ставь ⭐** и не пропусти регулярные обновления для поддержания актуальности скрипта и оптимальной автоматизации

> USDT TRC20: TL6gHETnKqNWV4D6GjiKKahkBsAwcyWfo8

<p align=center>
    <a href="https://t.me/grand_van" target="_blank" rel="noopener noreferrer">
        <img src="https://img.shields.io/badge/Telegram-GrandVan-purple?logo=telegram&logoColor=white&labelColor=blue" alt="Chat me on Telegram">
    </a>
</p>