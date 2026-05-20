import json
import os
from unittest.mock import patch

import pytest
from textual.widgets import ContentSwitcher

from evm_rpc_picker.screens.main_screen import MainScreen
from evm_rpc_picker.tabs.chainlist_tab import ChainlistTab
from evm_rpc_picker.tabs.env_rpcs_tab import EnvRPCTab
from evm_rpc_picker.tui import ChainRPCPicker
from evm_rpc_picker.widgets.chains_table import ChainsTable
from evm_rpc_picker.widgets.search_input import SearchInput

# Mock data
MOCK_CHAINS = [
    {
        "name": "Ethereum Mainnet",
        "chainId": 1,
        "shortName": "eth",
        "nativeCurrency": {"symbol": "ETH"},
        "rpc": ["https://eth-mainnet.public.blastapi.io", "https://rpc.ankr.com/eth"],
        "isTestnet": False,
    },
    {
        "name": "Sepolia",
        "chainId": 11155111,
        "shortName": "sep",
        "nativeCurrency": {"symbol": "ETH"},
        "rpc": ["https://rpc.sepolia.org"],
        "isTestnet": True,
    },
]


@pytest.fixture(autouse=True)
def mock_cache_file(tmp_path):
    # This fixture will run for every test and set a separate cache file
    cache_path = tmp_path / "test_chains.json"
    os.environ["EVM_RPC_PICKER_CACHE_FILE"] = str(cache_path)

    # Pre-populate cache to avoid network calls
    with open(cache_path, "w") as f:
        json.dump(MOCK_CHAINS, f)

    global_dir = tmp_path / "global"
    global_dir.mkdir()
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    local_file = local_dir / ".rpc-picker.toml"

    # Create an empty local config to avoid ConfirmModal
    local_file.write_text("[favorite_chains]\n")

    with (
        patch("evm_rpc_picker.config.user_config_dir", return_value=str(global_dir)),
        patch("evm_rpc_picker.config.ConfigManager.LOCAL_CONFIG_FILE", local_file),
        patch(
            "evm_rpc_picker.config.ConfigManager.GLOBAL_CONFIG_FILE",
            global_dir / "config.toml",
        ),
    ):
        yield


@pytest.mark.asyncio
async def test_app_initial_load():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        # Check current screen
        assert isinstance(app.screen, MainScreen)
        table = app.screen.query_one(ChainsTable)
        # Should have 2 mock chains
        assert table.row_count == 2


@pytest.mark.asyncio
async def test_search_filtering():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        # Type "Sep"
        for char in "sepolia":
            await pilot.press(char)
        await pilot.pause(0.2)

        table = app.screen.query_one(ChainsTable)
        assert table.row_count == 1


@pytest.mark.asyncio
async def test_filter_toggle():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        tab = app.screen.query_one(ChainlistTab)
        table = tab.query_one(ChainsTable)

        assert tab.filter_type == "all"
        await pilot.press("ctrl+t")
        await pilot.pause(0.2)
        assert tab.filter_type == "testnet"
        assert table.row_count == 1

        await pilot.press("ctrl+t")
        await pilot.pause(0.2)
        assert tab.filter_type == "mainnet"
        assert table.row_count == 1

        await pilot.press("ctrl+t")
        await pilot.pause(0.2)
        assert tab.filter_type == "all"
        assert table.row_count == 2


@pytest.mark.asyncio
async def test_env_rpcs_tab_loading():
    with patch.dict(
        os.environ,
        {"ETH_RPC_URL": "https://rpc.ankr.com/eth", "ANVIL_RPC_URL": "http://127.0.0.1:8545"},
    ):
        app = ChainRPCPicker()
        async with app.run_test() as pilot:
            await pilot.pause(0.5)
            # Switch to Env RPCs tab
            await pilot.press("ctrl+e")
            await pilot.pause(0.5)

            switcher = app.screen.query_one(ContentSwitcher)
            assert switcher.current == "tab-env"

            tab = app.screen.query_one(EnvRPCTab)
            assert tab is not None
            vars_present = [x["name"] for x in tab.env_rpcs]
            assert "ETH_RPC_URL" in vars_present
            assert "ANVIL_RPC_URL" in vars_present


@pytest.mark.asyncio
async def test_env_rpcs_tab_enter_select():
    with patch.dict(os.environ, {"ETH_RPC_URL": "https://rpc.ankr.com/eth"}):
        app = ChainRPCPicker()
        async with app.run_test() as pilot:
            await pilot.pause(0.5)
            # Switch to Env RPCs tab
            await pilot.press("ctrl+e")
            await pilot.pause(0.5)

            tab = app.screen.query_one(EnvRPCTab)
            tab.table.focus()

            with patch.object(app, "exit") as mock_exit:
                await pilot.press("enter")
                await pilot.pause(0.2)
                mock_exit.assert_called_once_with("https://rpc.ankr.com/eth")


@pytest.mark.asyncio
async def test_type_to_search_from_table():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        table = app.screen.query_one(ChainsTable)
        table.focus()

        await pilot.press("s")
        await pilot.press("e")
        await pilot.press("p")
        await pilot.pause(0.2)

        search_input = app.screen.query_one("#search-input", SearchInput)
        assert search_input.value == "sep"


@pytest.mark.asyncio
async def test_favorite_toggle():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        tab = app.screen.query_one(ChainlistTab)
        table = tab.query_one(ChainsTable)
        table.focus()
        table.move_cursor(row=0)

        with patch.object(app.config, "toggle_favorite") as mock_toggle:
            await tab.run_action("toggle_favorite")
            await pilot.pause(0.2)
            mock_toggle.assert_called()


@pytest.mark.asyncio
async def test_slash_is_typed_into_search():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        table = app.screen.query_one(ChainsTable)
        table.focus()

        await pilot.press("slash")
        await pilot.pause(0.2)

        search_input = app.screen.query_one("#search-input")
        assert search_input.value == "/"
        assert app.focused == table


@pytest.mark.asyncio
async def test_esc_clears_search_then_quits():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        search_input = app.screen.query_one("#search-input")

        # 1. Type something
        await pilot.press("a")
        assert search_input.value == "a"

        # 2. First ESC clears search
        await pilot.press("escape")
        assert search_input.value == ""

        # 3. Second ESC quits
        with patch.object(app, "exit") as mock_exit:
            await pilot.press("escape")
            await pilot.pause(0.2)
            mock_exit.assert_called_once()


@pytest.mark.asyncio
async def test_backspace_clears_search():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        search_input = app.screen.query_one("#search-input")

        await pilot.press("a")
        await pilot.press("b")
        assert search_input.value == "ab"

        await pilot.press("backspace")
        assert search_input.value == "a"

        await pilot.press("backspace")
        assert search_input.value == ""


@pytest.mark.asyncio
async def test_enter_favorite_rpcs_screen():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)

        await pilot.press("ctrl+b")
        await pilot.pause(0.5)

        switcher = app.screen.query_one(ContentSwitcher)
        assert switcher.current == "tab-favorites"


@pytest.mark.asyncio
async def test_tab_switch_focus():
    """Test that switching tabs via keyboard correctly focuses the table."""
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)

        # Switch to favorites via shortcut
        await pilot.press("ctrl+b")
        await pilot.pause(1.0)

        from textual.widgets import ContentSwitcher, DataTable

        switcher = app.screen.query_one(ContentSwitcher)
        assert switcher.current == "tab-favorites"

        # Verify focus is on the table in the new tab
        active_tab = app.screen.query_one("#tab-favorites")
        table = active_tab.query_one(DataTable)
        assert table.has_focus


@pytest.mark.asyncio
async def test_tab_click_no_crash():
    """Test that clicking a tab doesn't crash (mouse event propagation)."""
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause(0.5)

        # Try to click the favorites tab
        # We use a selector that is likely to hit the target
        await pilot.click("#tab-favorites")
        await pilot.pause(0.5)

        # We don't strictly assert the switch here if pilot.click is finicky,
        # but we MUST assert that no command palette is open (which would mean crash/bug)
        assert not app.query("CommandPalette")
