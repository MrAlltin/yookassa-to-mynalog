import json
import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from conftest import make_payment, make_refund


@pytest.fixture
def manager(tmp_path):
    """SyncManager с изолированным state-файлом во временной директории."""
    with patch("main.Configuration"), \
         patch("main.MoyNalogAPI") as mock_nalog_cls:
        mock_nalog_cls.return_value = AsyncMock()
        from main import SyncManager
        mgr = SyncManager.__new__(SyncManager)
        mgr.notifier = None
        mgr.nalog = AsyncMock()
        mgr.state_file = str(tmp_path / "sync_state.json")
        mgr.state = {
            "last_sync_time": "2026-01-01T00:00:00Z",
            "processed_payments": [],
            "pending_payments": [],
            "receipt_map": {},
            "processed_refunds": [],
            "last_refund_sync_time": None,
        }
        return mgr


class TestLoadState:
    def test_returns_fresh_state_when_no_file(self, manager):
        assert not os.path.exists(manager.state_file)
        from main import SyncManager
        state = SyncManager.load_state(manager)
        assert "processed_payments" in state
        assert "receipt_map" in state

    def test_loads_existing_valid_file(self, manager, tmp_path):
        data = {
            "last_sync_time": "2026-03-01T00:00:00Z",
            "processed_payments": ["pay-001"],
            "pending_payments": [],
            "receipt_map": {"pay-001": "receipt-001"},
            "processed_refunds": [],
            "last_refund_sync_time": None,
        }
        (tmp_path / "sync_state.json").write_text(json.dumps(data))
        from main import SyncManager
        state = SyncManager.load_state(manager)
        assert state["last_sync_time"] == "2026-03-01T00:00:00Z"
        assert "pay-001" in state["processed_payments"]

    def test_raises_on_corrupted_file(self, manager, tmp_path):
        (tmp_path / "sync_state.json").write_text("{ не валидный json }")
        from main import SyncManager
        with pytest.raises(RuntimeError, match="Повреждён файл состояния"):
            SyncManager.load_state(manager)

    def test_raises_on_empty_file(self, manager, tmp_path):
        (tmp_path / "sync_state.json").write_text("")
        from main import SyncManager
        with pytest.raises(RuntimeError):
            SyncManager.load_state(manager)

    def test_ensure_state_fields_adds_missing_keys(self, manager, tmp_path):
        # Файл без новых полей (старая версия state)
        data = {
            "last_sync_time": "2026-01-01T00:00:00Z",
            "processed_payments": [],
        }
        (tmp_path / "sync_state.json").write_text(json.dumps(data))
        from main import SyncManager
        state = SyncManager.load_state(manager)
        assert "pending_payments" in state
        assert "receipt_map" in state
        assert "processed_refunds" in state
        assert "last_refund_sync_time" in state


class TestSaveState:
    def test_creates_file(self, manager):
        from main import SyncManager
        SyncManager.save_state(manager)
        assert os.path.exists(manager.state_file)

    def test_saved_content_is_valid_json(self, manager):
        from main import SyncManager
        manager.state["processed_payments"] = ["pay-001", "pay-002"]
        SyncManager.save_state(manager)
        with open(manager.state_file) as f:
            loaded = json.load(f)
        assert loaded["processed_payments"] == ["pay-001", "pay-002"]

    def test_no_tmp_file_left_after_save(self, manager):
        from main import SyncManager
        SyncManager.save_state(manager)
        assert not os.path.exists(manager.state_file + ".tmp")

    def test_atomic_replace_preserves_old_on_write_error(self, manager, tmp_path):
        """Если запись во .tmp падает — оригинал не тронут."""
        original_data = {"last_sync_time": "2026-01-01T00:00:00Z", "processed_payments": ["original"]}
        (tmp_path / "sync_state.json").write_text(json.dumps(original_data))

        from main import SyncManager
        manager.state["processed_payments"] = ["new_data"]

        with patch("builtins.open", side_effect=OSError("disk full")):
            with pytest.raises(OSError):
                SyncManager.save_state(manager)

        # Оригинал не тронут
        with open(manager.state_file) as f:
            saved = json.load(f)
        assert saved["processed_payments"] == ["original"]


class TestGetNewYookassaPayments:
    @pytest.mark.asyncio
    async def test_returns_new_payments(self, manager):
        pay1 = make_payment("pay-001")
        pay2 = make_payment("pay-002")
        mock_res = MagicMock()
        mock_res.items = [pay1, pay2]
        mock_res.next_cursor = None

        with patch("main.Payment.list", return_value=mock_res):
            from main import SyncManager
            result = await SyncManager.get_new_yookassa_payments(manager)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_skips_already_processed(self, manager):
        manager.state["processed_payments"] = ["pay-001"]
        pay1 = make_payment("pay-001")
        pay2 = make_payment("pay-002")
        mock_res = MagicMock()
        mock_res.items = [pay1, pay2]
        mock_res.next_cursor = None

        with patch("main.Payment.list", return_value=mock_res):
            from main import SyncManager
            result = await SyncManager.get_new_yookassa_payments(manager)

        assert len(result) == 1
        assert result[0].id == "pay-002"

    @pytest.mark.asyncio
    async def test_skips_pending_payments(self, manager):
        manager.state["pending_payments"] = ["pay-001"]
        pay1 = make_payment("pay-001")
        mock_res = MagicMock()
        mock_res.items = [pay1]
        mock_res.next_cursor = None

        with patch("main.Payment.list", return_value=mock_res):
            from main import SyncManager
            result = await SyncManager.get_new_yookassa_payments(manager)

        assert result == []

    @pytest.mark.asyncio
    async def test_handles_pagination(self, manager):
        pay1 = make_payment("pay-001")
        pay2 = make_payment("pay-002")

        page1 = MagicMock()
        page1.items = [pay1]
        page1.next_cursor = "cursor-abc"

        page2 = MagicMock()
        page2.items = [pay2]
        page2.next_cursor = None

        with patch("main.Payment.list", side_effect=[page1, page2]):
            from main import SyncManager
            result = await SyncManager.get_new_yookassa_payments(manager)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_on_api_error(self, manager):
        with patch("main.Payment.list", side_effect=Exception("API недоступен")):
            from main import SyncManager
            result = await SyncManager.get_new_yookassa_payments(manager)

        assert result == []


class TestGetNewRefunds:
    @pytest.mark.asyncio
    async def test_returns_new_refunds(self, manager):
        ref1 = make_refund("ref-001", "pay-001")
        mock_res = MagicMock()
        mock_res.items = [ref1]
        mock_res.next_cursor = None

        with patch("main.Refund.list", return_value=mock_res):
            from main import SyncManager
            result = await SyncManager.get_new_refunds(manager)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_skips_already_processed_refunds(self, manager):
        manager.state["processed_refunds"] = ["ref-001"]
        ref1 = make_refund("ref-001")
        mock_res = MagicMock()
        mock_res.items = [ref1]
        mock_res.next_cursor = None

        with patch("main.Refund.list", return_value=mock_res):
            from main import SyncManager
            result = await SyncManager.get_new_refunds(manager)

        assert result == []

    @pytest.mark.asyncio
    async def test_uses_last_refund_sync_time_if_set(self, manager):
        manager.state["last_refund_sync_time"] = "2026-02-01T00:00:00Z"
        mock_res = MagicMock()
        mock_res.items = []
        mock_res.next_cursor = None

        with patch("main.Refund.list", return_value=mock_res) as mock_list:
            from main import SyncManager
            await SyncManager.get_new_refunds(manager)

        called_params = mock_list.call_args[0][0]
        assert called_params["created_at.gte"] == "2026-02-01T00:00:00Z"

    @pytest.mark.asyncio
    async def test_falls_back_to_last_sync_time(self, manager):
        manager.state["last_refund_sync_time"] = None
        manager.state["last_sync_time"] = "2026-01-01T00:00:00Z"
        mock_res = MagicMock()
        mock_res.items = []
        mock_res.next_cursor = None

        with patch("main.Refund.list", return_value=mock_res) as mock_list:
            from main import SyncManager
            await SyncManager.get_new_refunds(manager)

        called_params = mock_list.call_args[0][0]
        assert called_params["created_at.gte"] == "2026-01-01T00:00:00Z"
