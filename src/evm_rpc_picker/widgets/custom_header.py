import contextlib
from typing import TYPE_CHECKING, Any

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Label, Tab, Tabs

if TYPE_CHECKING:
    from ..tui import ChainRPCPicker


class CustomHeader(Horizontal):
    """2-row header with icon, title, embedded tabs and subtitle."""

    app: "ChainRPCPicker"  # pyrefly: ignore[bad-override]

    privacy_mode: reactive[bool] = reactive(False)

    DEFAULT_CSS = """
    CustomHeader {
        height: 2;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 2;
    }
    #header-title, #header-title-short {
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
    #header-subtitle, #header-subtitle-short {
        width: auto;
        height: 2;
        content-align: right top;
        text-style: italic;
        color: #6c7086;
        margin-left: 2;
    }
    #header-subtitle-privacy, #header-subtitle-privacy-short {
        width: auto;
        height: 2;
        content-align: right top;
        text-style: bold;
        color: #f38ba8;
        margin-left: 2;
    }
    #header-title-short {
        display: none;
    }
    #header-subtitle-short {
        display: none;
    }
    #header-subtitle-privacy {
        display: none;
    }
    #header-subtitle-privacy-short {
        display: none;
    }
    """

    def __init__(
        self, title: str = "Ξ EVM RPC Picker", show_tabs: bool = False, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self._header_title = title
        self._show_tabs = show_tabs

    def compose(self) -> ComposeResult:
        yield Label(self._header_title, id="header-title", classes="palette-trigger")
        yield Label("Ξ", id="header-title-short", classes="palette-trigger")
        if self._show_tabs:
            yield Tabs(
                Tab("Chainlist.org [^N]", id="tab-chainlist"),
                Tab("Personal RPC URLs [^U]", id="tab-personal"),
                Tab("★ Favorite RPCs [^B]", id="tab-favorites"),
                Tab("Env RPCs [^E]", id="tab-env"),
                id="main-tabs",
            )
        else:
            # Empty spacer to keep subtitle on the right
            yield Label("", id="main-tabs")
        yield Label("CU @ 🍻 BeerFi Prague", id="header-subtitle", classes="palette-trigger")
        yield Label("🍻", id="header-subtitle-short", classes="palette-trigger")
        yield Label("[🙈] Sensitive Mode", id="header-subtitle-privacy")
        yield Label("[🙈]", id="header-subtitle-privacy-short")

    def on_mount(self) -> None:
        """Sync initial privacy mode state from app after mount."""
        with contextlib.suppress(Exception):
            self.watch(self.app, "privacy_mode", self._update_privacy, init=True)

    def _update_privacy(self, privacy: bool) -> None:
        """Update reactive state of header."""
        self.privacy_mode = privacy

    def on_resize(self, event: events.Resize) -> None:
        with contextlib.suppress(Exception):
            privacy: bool = self.privacy_mode
            if event.size.width < 110:
                self.query_one("#header-title", Label).display = False
                self.query_one("#header-title-short", Label).display = True
                self._apply_privacy(privacy, narrow=True)
            else:
                self.query_one("#header-title", Label).display = True
                self.query_one("#header-title-short", Label).display = False
                self._apply_privacy(privacy, narrow=False)

        if not self._show_tabs:
            return
        with contextlib.suppress(Exception):
            if event.size.width < 110:
                self.query_one("#tab-chainlist", Tab).update("Chainlist [^N]")
                self.query_one("#tab-personal", Tab).update("Personal [^U]")
                self.query_one("#tab-favorites", Tab).update("Favs [^B]")
                self.query_one("#tab-env", Tab).update("Envs [^E]")
            else:
                self.query_one("#tab-chainlist", Tab).update("Chainlist.org [^N]")
                self.query_one("#tab-personal", Tab).update("Personal RPC URLs [^U]")
                self.query_one("#tab-favorites", Tab).update("★ Favorite RPCs [^B]")
                self.query_one("#tab-env", Tab).update("Env RPCs [^E]")

    def _apply_privacy(self, privacy: bool, narrow: bool | None = None) -> None:
        """Show/hide subtitle vs. privacy indicator labels according to mode."""
        with contextlib.suppress(Exception):
            # Determine narrow state if not provided explicitly
            if narrow is None:
                try:
                    narrow = self.size.width < 110
                except Exception:
                    narrow = False

            self.query_one("#header-subtitle", Label).display = not privacy and not narrow
            self.query_one("#header-subtitle-short", Label).display = not privacy and narrow
            self.query_one("#header-subtitle-privacy", Label).display = privacy and not narrow
            self.query_one("#header-subtitle-privacy-short", Label).display = privacy and narrow

    def watch_privacy_mode(self, privacy: bool) -> None:
        """Called automatically when app.privacy_mode changes."""
        self._apply_privacy(privacy)

    @on(events.Click, ".palette-trigger")
    def on_trigger_click(self, event: events.Click) -> None:
        """Open the command palette when the header text is clicked."""
        self.app.action_command_palette()
        event.stop()
