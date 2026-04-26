from textual.app import App

from .config import ConfigManager
from .screens import MainScreen


class ChainRPCPicker(App[str]):
    """TUI to search chains and select RPC URL."""

    TITLE = "EVM RPC Picker"

    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()

    CSS = """
    Screen {
        background: #11111b;
    }

    Header {
        background: #1e1e2e;
        color: #89b4fa;
        text-style: bold;
    }

    Footer {
        background: #1e1e2e;
        color: #cdd6f4;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


if __name__ == "__main__":
    app = ChainRPCPicker()
    result = app.run()
    if result:
        print(result)
