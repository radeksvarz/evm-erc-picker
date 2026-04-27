from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label


class CustomHeader(Horizontal):
    """1-row header with icon, title and subtitle instead of clock."""

    DEFAULT_CSS = """
    CustomHeader {
        height: 1;
        background: #313244;
        color: #cdd6f4;
        padding: 0 2;
        text-style: bold;
    }
    #header-title {
        width: auto;
    }
    #header-subtitle {
        width: 1fr;
        text-align: right;
        text-style: italic;
        color: #9399b2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Ξ EVM RPC Picker", id="header-title")
        yield Label("CU @ 🍻 BeerFi Prague", id="header-subtitle")

    def on_click(self) -> None:
        """Open the command palette when the header is clicked."""
        self.app.action_command_palette()
