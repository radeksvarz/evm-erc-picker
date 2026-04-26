from .tui import ChainRPCPicker

def pick_rpc() -> str:
    """
    Run the EVM RPC Picker TUI and return the selected RPC URL.
    Returns an empty string if the user cancels.
    """
    app = ChainRPCPicker()
    return app.run()
