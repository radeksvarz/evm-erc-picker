from typing import Optional
from .tui import ChainRPCPicker


def pick_rpc() -> Optional[str]:
    """
    Run the EVM RPC Picker TUI and return the selected RPC URL.
    Returns None if the user cancels.
    """
    app = ChainRPCPicker()
    return app.run()
