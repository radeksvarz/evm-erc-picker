import contextlib

from textual.app import App
from textual.reactive import reactive

from .config import ConfigManager
from .screens import MainScreen


class ChainRPCPicker(App[str]):
    """TUI to search chains and select RPC URL."""

    TITLE = "EVM RPC Picker"

    privacy_mode: reactive[bool] = reactive(False)

    def __init__(self, privacy: bool = False) -> None:
        super().__init__()
        self.config = ConfigManager()
        self._initial_privacy = privacy

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
        """Mount main screen and apply initial privacy mode."""
        self.privacy_mode = self._initial_privacy
        self.push_screen(MainScreen())

    def action_toggle_privacy(self) -> None:
        """Toggle privacy (sensitive) mode on/off."""
        self.privacy_mode = not self.privacy_mode
        state = "ON" if self.privacy_mode else "OFF"
        self.notify(
            f"Sensitive Mode is now {state}.",
            title="Sensitive Mode",
            severity="warning" if self.privacy_mode else "information",
        )
        with contextlib.suppress(Exception):
            screen = self.screen
            if hasattr(screen, "refresh_active_tab"):
                screen.refresh_active_tab()


if __name__ == "__main__":
    app = ChainRPCPicker()
    result = app.run()
    if result:
        print(result)
