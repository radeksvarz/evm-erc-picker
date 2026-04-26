import os
import json
import pytest
from unittest.mock import patch, MagicMock
from evm_rpc_picker.tui import ChainRPCPicker
from evm_rpc_picker.widgets.search_input import SearchInput
from evm_rpc_picker.widgets.chains_table import ChainsTable
from evm_rpc_picker.widgets.env_status import EnvStatus
from evm_rpc_picker.screens.main_screen import MainScreen
from evm_rpc_picker.screens.rpc_screen import RPCScreen

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
    local_file = tmp_path / "local" / ".rpc-picker.toml"
    local_file.parent.mkdir()

    with (
        patch("evm_rpc_picker.config.user_config_dir", return_value=str(global_dir)),
        patch("evm_rpc_picker.config.ConfigManager.LOCAL_CONFIG_FILE", local_file),
        patch(
            "evm_rpc_picker.config.ConfigManager.GLOBAL_CONFIG_FILE",
            global_dir / "config.json",
        ),
        patch(
            "evm_rpc_picker.context.ContextDetector.get_context_chain_names",
            return_value=set(),
        ),
        patch(
            "evm_rpc_picker.context.ContextDetector.get_foundry_rpc_endpoints",
            return_value={},
        ),
    ):
        yield

    if "EVM_RPC_PICKER_CACHE_FILE" in os.environ:
        del os.environ["EVM_RPC_PICKER_CACHE_FILE"]


@pytest.mark.asyncio
async def test_app_starts():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.title == "EVM RPC Picker"
        assert isinstance(app.screen, MainScreen)


@pytest.mark.asyncio
async def test_search_filtering():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()
        main_screen = app.screen

        # Initial state
        assert len(main_screen.filtered_chains) == 2

        # Search for "sepolia"
        await pilot.press(*list("sepolia"))
        await pilot.pause()
        assert len(main_screen.filtered_chains) == 1
        assert main_screen.filtered_chains[0]["chainId"] == 11155111

        # Clear search (backspace)
        for _ in range(7):
            await pilot.press("backspace")
        await pilot.pause()
        assert len(main_screen.filtered_chains) == 2


@pytest.mark.asyncio
async def test_filter_toggle():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()
        main_screen = app.screen

        # Default -> ALL (2 chains)
        assert main_screen.filter_mode == "all"
        assert len(main_screen.filtered_chains) == 2

        # Press Ctrl+T -> MAINNET (1 chain)
        await pilot.press("ctrl+t")
        assert main_screen.filter_mode == "mainnet"
        assert len(main_screen.filtered_chains) == 1
        assert main_screen.filtered_chains[0]["chainId"] == 1

        # Press Ctrl+T -> TESTNET (1 chain)
        await pilot.press("ctrl+t")
        assert main_screen.filter_mode == "testnet"
        assert len(main_screen.filtered_chains) == 1
        assert main_screen.filtered_chains[0]["chainId"] == 11155111

        # Press Ctrl+T -> FAVORITES (0 chains by default)
        await pilot.press("ctrl+t")
        assert main_screen.filter_mode == "favorites"
        assert len(main_screen.filtered_chains) == 0

        # Press Ctrl+T -> ALL again
        await pilot.press("ctrl+t")
        assert main_screen.filter_mode == "all"


@pytest.mark.asyncio
async def test_navigation_to_rpc_screen():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Focus table and press Enter
        await pilot.press("tab")
        await pilot.press("enter")
        await pilot.pause()

        # Should now be on RPCScreen
        assert isinstance(app.screen, RPCScreen)
        assert app.screen.chain["name"] == "Ethereum Mainnet"


@pytest.mark.asyncio
async def test_rpc_screen_back_navigation():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Enter RPCScreen
        await pilot.press("tab", "enter")
        await pilot.pause()
        assert isinstance(app.screen, RPCScreen)

        # Press ESC to go back
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainScreen)


@pytest.mark.asyncio
async def test_rpc_selection_and_exit():
    app = ChainRPCPicker()
    # Mock ping_rpc instead of check_latencies to let the sorting/selection logic run
    with patch(
        "evm_rpc_picker.screens.rpc_screen.RPCScreen.ping_rpc", return_value=None
    ):
        async with app.run_test() as pilot:
            await pilot.pause()

            # Select first chain (Ethereum)
            await pilot.press("tab", "enter")
            # Wait for RPCScreen to mount and run workers and set index
            await pilot.pause(0.5)

            # Select first RPC
            await pilot.press("enter")
            await pilot.pause(0.5)

            # The app should have exited with one of the URLs
            assert app.return_value in [
                "https://eth-mainnet.public.blastapi.io",
                "https://rpc.ankr.com/eth",
            ]


@pytest.mark.asyncio
async def test_env_status_widget_latency():
    # Mock ETH_RPC_URL and the network response
    with patch.dict(os.environ, {"ETH_RPC_URL": "https://mock-rpc.com"}):
        with patch("httpx.AsyncClient.post") as mock_post:
            # Mock a successful RPC response
            mock_post.return_value = MagicMock(status_code=200)

            app = ChainRPCPicker()
            async with app.run_test() as pilot:
                await pilot.pause()
                # Give the worker a moment to finish
                import asyncio

                await asyncio.sleep(0.1)

                env_status = app.screen.query_one(EnvStatus)
                # Access .content for assertion (confirmed via debug)
                latency_text = str(env_status.latency_label.content)
                status_text = str(env_status.status_label.content)
                assert "ms" in latency_text
                assert "https://mock-rpc.com" in status_text


@pytest.mark.asyncio
async def test_env_status_widget_enter_select():
    # Mock ETH_RPC_URL
    rpc_url = "https://current-rpc.com"
    with patch.dict(os.environ, {"ETH_RPC_URL": rpc_url}):
        app = ChainRPCPicker()
        async with app.run_test() as pilot:
            await pilot.pause()
            # Tab to the widget
            await pilot.press("tab", "tab")
            assert app.focused.id == "env-status-widget"

            # Press Enter
            await pilot.press("enter")
            await pilot.pause()

            # App should return the URL
            assert app.return_value == rpc_url


@pytest.mark.asyncio
async def test_type_to_search_from_table():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Move focus to table
        await pilot.press("tab")
        assert isinstance(app.focused, ChainsTable)

        # Type "s" (start of Sepolia)
        await pilot.press("s")
        await pilot.pause()

        # Focus should have jumped
        assert isinstance(app.focused, SearchInput)
        assert app.focused.value == "s"

        # Type "e" (start of Sepolia)
        await pilot.press("e")
        await pilot.pause()

        assert app.focused.value == "se"


@pytest.mark.asyncio
async def test_favorite_toggle():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()
        main_screen = app.screen

        # Select first chain (Ethereum, ID 1)
        await pilot.press("tab")  # focus table
        await pilot.press("shift+space")  # global favorite
        await pilot.pause()

        # Verify it's in global favorites
        assert 1 in main_screen.config.get_favorites(project_only=False)

        # Toggle filter to favorites
        await pilot.press("ctrl+t", "ctrl+t", "ctrl+t")
        assert main_screen.filter_mode == "favorites"
        assert len(main_screen.filtered_chains) == 1
        assert main_screen.filtered_chains[0]["chainId"] == 1

        # Remove from favorites
        await pilot.press("shift+space")
        await pilot.pause()
        assert 1 not in main_screen.config.get_favorites(project_only=False)
        assert len(main_screen.filtered_chains) == 0


@pytest.mark.asyncio
async def test_slash_focuses_search_without_typing():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Move focus to table
        await pilot.press("tab")
        assert isinstance(app.focused, ChainsTable)

        # Press "/"
        await pilot.press("/")
        await pilot.pause()

        # Focus should have jumped but value should be EMPTY
        assert isinstance(app.focused, SearchInput)
        assert app.focused.value == ""


@pytest.mark.asyncio
async def test_quit_on_esc():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.press("escape")
        assert not app.is_running
