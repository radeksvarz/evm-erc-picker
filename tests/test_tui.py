import os
import pytest
from evm_rpc_picker.tui import ChainRPCPicker
from evm_rpc_picker.widgets.search_input import SearchInput
from evm_rpc_picker.widgets.chains_table import ChainsTable

@pytest.fixture(autouse=True)
def mock_cache_file(tmp_path):
    # This fixture will run for every test and set a separate cache file
    os.environ["EVM_RPC_PICKER_CACHE_FILE"] = str(tmp_path / "test_chains.json")
    yield
    if "EVM_RPC_PICKER_CACHE_FILE" in os.environ:
        del os.environ["EVM_RPC_PICKER_CACHE_FILE"]

@pytest.mark.asyncio
async def test_app_focus_cycling():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        # Check initial focus
        assert isinstance(app.focused, SearchInput)
        
        # Press Tab to move to table
        await pilot.press("tab")
        assert isinstance(app.focused, ChainsTable)
        
        # Press Tab to move to env status
        await pilot.press("tab")
        assert app.focused.id == "env-status"
        
        # Press Tab to wrap back to SearchInput
        await pilot.press("tab")
        assert isinstance(app.focused, SearchInput)

@pytest.mark.asyncio
async def test_search_filtering():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        # Wait for data to load
        await pilot.pause()
        
        # We simulate typing in search
        await pilot.press(*"ethereum")
        
        # Get the main screen and check filtered chains
        main_screen = app.screen
        # Check that filtering logic is working
        assert len(main_screen.filtered_chains) > 0

@pytest.mark.asyncio
async def test_quit_on_esc():
    app = ChainRPCPicker()
    async with app.run_test() as pilot:
        await pilot.press("escape")
        # App should be closing or closed
        assert not app.is_running
