from typing import Any

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, Tab, Tabs


class CustomHeader(Horizontal):
    """2-row header with icon, title, embedded tabs and subtitle."""

    DEFAULT_CSS = """
    CustomHeader {
        height: 2;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 2;
    }
    #header-title {
        width: auto;
        height: 2;
        content-align: left top;
        text-style: bold;
        color: #f5e0dc;
    }
    #main-tabs {
        width: 1fr;
        height: 2;
        background: transparent;
        border: none;
        min-width: 40;
    }
    #main-tabs > Underline {
        background: #313244;
        color: #89b4fa;
        height: 1;
    }
    #main-tabs Tab {
        padding: 0 2;
        height: 1;
        color: #9399b2;
        text-style: none;
        background: transparent;
    }
    #main-tabs Tab.--active {
        background: #89b4fa;
        color: #11111b;
        text-style: bold;
    }
    #main-tabs Tab:hover {
        background: #45475a;
        color: #f5e0dc;
    }
    #header-subtitle {
        width: auto;
        height: 2;
        content-align: right top;
        text-style: italic;
        color: #6c7086;
        margin-left: 2;
    }
    """

    def __init__(self, title: str = "Ξ EVM RPC Picker", show_tabs: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._header_title = title
        self._show_tabs = show_tabs

    def compose(self) -> ComposeResult:
        yield Label(self._header_title, id="header-title", classes="palette-trigger")
        if self._show_tabs:
            yield Tabs(
                Tab("Chainlist.org [^N]", id="tab-chainlist"),
                Tab("Personal RPC URLs [^U]", id="tab-personal"),
                Tab("★ Favorite RPCs [^B]", id="tab-favorites"),
                id="main-tabs"
            )
        else:
            # Empty spacer to keep subtitle on the right
            yield Label("", id="main-tabs")
        yield Label("CU @ 🍻 BeerFi Prague", id="header-subtitle", classes="palette-trigger")

    @on(events.Click, ".palette-trigger")
    def on_trigger_click(self, event: events.Click) -> None:
        """Open the command palette when the header text is clicked."""
        self.app.action_command_palette()
        event.stop()
